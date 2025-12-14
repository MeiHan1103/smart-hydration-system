# Smart Hydration System 智慧飲水提醒系統 --- ## 介紹（Overview） 現代人因長時間工作或讀書，常常忽略飲水，導致身體不適甚至影響健康。 本專題「Smart Hydration Central」旨在透過 IoT 技術，協助使用者即時掌握自身飲水狀況， 並透過系統提醒與紀錄功能，培養良好的飲水習慣。 系統適用於固定桌面環境（如書桌、辦公桌）， 結合實體顯示（LCD）與 Web 儀表板， 讓使用者能直觀掌握自己的飲水狀況，建立良好飲水習慣。。 --- ## 系統功能（Features） - 即時量測水壺重量並換算為水量（ml） - 自動判斷飲水事件並記錄飲水量 - 追蹤今日累積飲水量與距離上次飲水時間 - LCD 顯示即時狀態與提醒訊息 - Web 儀表板顯示即時狀態、歷史紀錄與飲水趨勢 - 支援多水壺管理 --- ## 硬體需求（Hardware Requirements） - Raspberry Pi 4 - Load Cell - HX711 重量感測模組 - I2C LCD 顯示器（20x4） - 壓克力板 - 杜邦線 - USB 電源線 --- ## 智慧杯墊結構說明 本系統將 Load Cell 夾設於上下兩塊壓克力板之間， 形成穩定的「智慧杯墊」結構。 - 上層壓克力板：放置水壺 - 中間 Load Cell：量測重量變化 - 下層壓克力板：固定與支撐 此結構可避免水壺直接壓迫感測器造成偏移， 並提升長時間使用的穩定性。 --- ## 硬體接線說明（Wiring） ### Load Cell → HX711 | Load Cell 線色 | HX711 腳位 | |---------------|-----------| | 紅線 | E+ | | 黑線 | E- | | 白線 | A- | | 綠線 | A+ | ### HX711 → Raspberry Pi | HX711 | Raspberry Pi | |-----|--------------| | VCC | 5V | | GND | GND | | DT | GPIO 5 | | SCK | GPIO 6 | ### I2C LCD → Raspberry Pi | LCD | Raspberry Pi | |----|--------------| | VCC | 5V | | GND | GND | | SDA | GPIO 2 | | SCL | GPIO 3 | --- ## 軟體需求（Software Requirements） - 作業系統：Raspberry Pi OS - Python 版本：Python 3.7 以上 --- ## 安裝與執行步驟（Installation） ### 1️.更新系統
bash
sudo apt update
sudo apt upgrade
### 2.啟用 I2C
bash
sudo raspi-config
請依序選擇：
pgsql
Interface Options → I2C → Enable
完成後重新開機：
bash
sudo reboot
### 3.安裝 Python 套件
bash
pip3 install flask RPLCD hx711
### 4.執行系統 請先進入本專案資料夾：
bash
cd IOT
接著同時啟動感測系統與 Web Dashboard：
bash
python3 main.py & python3 app.py
- main.py： 負責讀取 Load Cell（秤重器）資料、判斷飲水狀態，並將資料寫入資料庫。 - app.py： 啟動 Flask Web Server，提供即時監控與管理介面。 ### 5.開啟 Web Dashboard 系統成功啟動後，請在瀏覽器輸入以下其中一個網址：
text
http://raspberrypi.local:5000
或（在樹莓派本機）：
text
http://localhost:5000
即可看到「智慧飲水系統」的即時監控畫面。 ### 6.系統停止方式 若要停止系統，請在終端機中按下：
text
Ctrl + C
