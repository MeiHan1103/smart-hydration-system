#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime

import RPi.GPIO as GPIO
from hx711 import HX711
from RPLCD.i2c import CharLCD

# ========== 新增：導入資料庫模組 ==========
import database as db

# =========================================================
# 設定區
# =========================================================

HX_DOUT = 5
HX_SCK  = 6

HX_OFFSET = -85927.1
HX_SCALE  = -465.719

LCD_ADDR = 0x27
LCD_COLS = 20
LCD_ROWS = 4

EMPTY_BOTTLE_G = None

DISPLAY_DEADBAND_ML = 5
NO_WATER_ML = 10
REMIND_MINS = 3  # 改成 3 分鐘方便測試
DRINK_EVENT_MIN_ML = 15
LIFT_DROP_G = 100
LIFT_MIN_PRESENT_G = -200
STABLE_VAR_G = 20

RAW_SAMPLES = 10
EMA_ALPHA = 0.3
LOOP_SEC = 0.3

# =========================================================
# LCD 顯示
# =========================================================

lcd = CharLCD(
    i2c_expander="PCF8574",
    address=LCD_ADDR,
    port=1,
    cols=LCD_COLS,
    rows=LCD_ROWS,
    charmap="A00"
)

def _pad(s: str, width: int = 20) -> str:
    return (s[:width]).ljust(width)

def _fmt_time() -> str:
    return datetime.now().strftime("%H:%M")

def lcd_show(status: str, water_ml: int, last_mins: int, today_ml: int, lifting: bool):
    now = _fmt_time()

    if lifting:
        line1 = f"{now}   DRINKING..."
    else:
        if status == "NO_WATER":
            line1 = f"{now}  NO WATER T_T"
        elif status == "DRINK":
            line1 = f"{now}  DRINK NOW >_<"
        else:
            line1 = f"{now}  Hydration OK ^_^"

    line2 = f"Water:{water_ml:4d} ml"
    line3 = f"Last:{last_mins:3d}m Today:{today_ml:4d}"

    if lifting:
        line4 = "Holding bottle..."
    else:
        if status == "NO_WATER":
            line4 = "Refill now!  T_T"
        elif status == "DRINK":
            line4 = "Take a sip! >_<"
        else:
            line4 = "Keep going! ^_^"

    lcd.cursor_pos = (0, 0); lcd.write_string(_pad(line1))
    lcd.cursor_pos = (1, 0); lcd.write_string(_pad(line2))
    lcd.cursor_pos = (2, 0); lcd.write_string(_pad(line3))
    lcd.cursor_pos = (3, 0); lcd.write_string(_pad(line4))

# =========================================================
# HX711 讀取
# =========================================================

def hx_read_raw_avg(hx: HX711, n: int = 10) -> float:
    data = hx.get_raw_data(n)
    if isinstance(data, list) and len(data) > 0:
        valid = [v for v in data if v is not False and v is not None]
        if valid:
            return sum(valid) / len(valid)
    return 0

def raw_to_grams(raw: float, offset: float, scale: float) -> float:
    return (raw - offset) / scale

# =========================================================
# 主程式
# =========================================================

def main():
    global EMPTY_BOTTLE_G

    print("=== 智慧飲水提醒系統 ===")
    print("按 Ctrl+C 停止\n")

    # ========== 新增：初始化資料庫 ==========
    db.init_database()

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    hx = HX711(dout_pin=HX_DOUT, pd_sck_pin=HX_SCK)
    hx.reset()
    time.sleep(0.5)

    print("正在測試 HX711 連線...")
    time.sleep(1)

    print("讀取測試中 (3 秒)...")
    for i in range(6):
        r = hx_read_raw_avg(hx, 3)
        g = raw_to_grams(r, HX_OFFSET, HX_SCALE)
        print(f"  [{i+1}/6] raw={r:.0f}, grams={g:.1f}")
        time.sleep(0.5)

    print("\n✓ HX711 讀取正常！")

    # ========== 新增：從資料庫讀取水壺資訊 ==========
    if EMPTY_BOTTLE_G is None:
        bottle = db.get_active_bottle()
        if bottle:
            EMPTY_BOTTLE_G = bottle['empty_weight']
            print(f"\n使用已儲存的水壺：{bottle['name']}")
            print(f"✓ 空壺重量 = {EMPTY_BOTTLE_G:.1f} g")
        else:
            print("\n⚠️  尚未設定水壺！")
            print("請先到網頁 http://raspberrypi.local:5000/bottles")
            print("新增並選擇一個水壺，然後重新執行程式。\n")
            GPIO.cleanup()
            return

    print("\n==================================================")
    print("系統開始監測...")
    print("==================================================\n")

    # ========== 新增：從資料庫讀取今日總量 ==========
    today_ml = db.get_today_total()
    print(f"今日已飲用：{today_ml} ml\n")

    # ========== 新增：從資料庫讀取設定 ==========
    settings = db.get_all_settings()
    remind_interval = int(settings.get('remind_interval_min', 60))

    ema_g = None
    last_display_ml = 0
    last_stable_ml = 0
    last_drink_ts = time.time()
    recent_g = []
    prev_ema_g = None

    try:
        while True:
            raw = hx_read_raw_avg(hx, RAW_SAMPLES)
            grams = raw_to_grams(raw, HX_OFFSET, HX_SCALE)

            # EMA 濾波（自適應）
            if ema_g is None:
                ema_g = grams
            else:
                change = abs(grams - ema_g)

                if change > 100:
                    alpha = 0.6
                elif change > 20:
                    alpha = 0.4
                else:
                    alpha = 0.2

                ema_g = (alpha * grams) + ((1 - alpha) * ema_g)

            recent_g.append(ema_g)
            if len(recent_g) > 8:
                recent_g.pop(0)

            g_min = min(recent_g) if recent_g else ema_g
            g_max = max(recent_g) if recent_g else ema_g
            g_var = g_max - g_min

            lifting = False
            if ema_g < LIFT_MIN_PRESENT_G:
                lifting = True
            if prev_ema_g is not None and (prev_ema_g - ema_g) > LIFT_DROP_G:
                lifting = True
            prev_ema_g = ema_g

            water_ml_float = ema_g - EMPTY_BOTTLE_G
            water_ml = int(round(max(0.0, water_ml_float)))

            stable = (g_var <= STABLE_VAR_G) and (not lifting)

            # ========== 修改：飲水事件判斷 + 寫入資料庫 ==========
            drank_ml = 0

            if stable and water_ml > 0:
                if last_stable_ml > 0:
                    drop = last_stable_ml - water_ml
                    if drop >= DRINK_EVENT_MIN_ML:
                        drank_ml = drop
                        today_ml += drank_ml
                        last_drink_ts = time.time()
                        print(f"  ★ 偵測到飲水事件！喝了 {drank_ml} ml")

                        # ========== 新增：寫入資料庫 ==========
                        try:
                            bottle = db.get_active_bottle()
                            bottle_id = bottle['id'] if bottle else None
                            db.add_drink_event(drank_ml, bottle_id)
                            print(f"  ✓ 已記錄到資料庫")
                        except Exception as e:
                            print(f"  ✗ 資料庫寫入失敗: {e}")

                last_stable_ml = water_ml

            if abs(water_ml - last_display_ml) >= DISPLAY_DEADBAND_ML:
                last_display_ml = water_ml
            else:
                water_ml = last_display_ml

            mins_since = int((time.time() - last_drink_ts) / 60)

            if lifting:
                status = "OK"
            else:
                if water_ml <= NO_WATER_ML and (stable or last_stable_ml <= NO_WATER_ML):
                    status = "NO_WATER"
                elif stable and mins_since >= remind_interval:
                    status = "DRINK"
                else:
                    status = "OK"

            lcd_show(
                status=status,
                water_ml=water_ml,
                last_mins=mins_since,
                today_ml=today_ml,
                lifting=lifting
            )

            # ========== 新增：更新資料庫狀態 ==========
            try:
                db.update_status(water_ml, status, mins_since, today_ml)
            except Exception:
                pass

            print(
                f"重={ema_g:6.1f}g 水={water_ml:4d}ml "
                f"穩={str(stable)[0]} 拿={str(lifting)[0]} 喝={drank_ml:3d}ml 今日={today_ml:4d}ml"
            )

            time.sleep(LOOP_SEC)

    except KeyboardInterrupt:
        print("\n\n系統停止")

    finally:
        try:
            lcd.clear()
        except:
            pass
        GPIO.cleanup()


if __name__ == "__main__":
    main()