# Python Project Setup Guide

## เริ่มต้นครั้งแรก (First Time Setup)

### 1. ติดตั้ง Python
```powershell
winget install Python.Python.3.13
```
**ปิด PowerShell แล้วเปิดใหม่**

### 2. ตรวจสอบการติดตั้ง
```powershell
python --version
```
ควรได้: `Python 3.13.x`

**ถ้า Error "Python was not found":**
```powershell
# ลบ Microsoft Store Alias
Remove-Item "$env:LOCALAPPDATA\Microsoft\WindowsApps\python*.exe"

# ปิด PowerShell แล้วเปิดใหม่
python --version
```

---

## Setup โปรเจค (Project Setup)

### 3. ไปที่โฟลเดอร์โปรเจค
```powershell
cd C:\path\to\your\project
```

### 4. สร้าง Virtual Environment
```powershell
# ลบ .venv เก่า (ถ้ามี)
Remove-Item -Recurse -Force .venv

# สร้างใหม่
python -m venv .venv
```

### 5. Activate Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```
จะเห็น `(.venv)` ข้างหน้า

**ถ้า Error Execution Policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

### 6. ติดตั้ง Dependencies
```powershell
pip install -r requirements.txt
```

### 7. รันโปรแกรม
```powershell
python src/main/login.py
```

---

## คำสั่งที่ใช้บ่อย (Common Commands)

### Virtual Environment
```powershell
# Activate
.venv\Scripts\Activate.ps1

# Deactivate
deactivate
```

### Package Management
```powershell
# ติดตั้ง package
pip install <package-name>

# ดู packages ที่ติดตั้ง
pip list

# สร้าง requirements.txt
pip freeze > requirements.txt
```

### รันโปรแกรม
```powershell
# ต้อง activate venv ก่อนเสมอ
.venv\Scripts\Activate.ps1
python src/main/login.py
```

---

## โครงสร้างโปรเจค (Project Structure)

```
year2project/
├── .venv/              # Virtual environment (ไม่ commit)
├── src/
│   └── main/
│       └── login.py
├── requirements.txt    # Dependencies list
└── .gitignore         # Git ignore file
```

### .gitignore
```gitignore
.venv/
__pycache__/
*.pyc
*.pyo
```

---

## Troubleshooting

### Python ไม่เจอหลังติดตั้ง
1. ปิด PowerShell ทุก window
2. เปิดใหม่
3. ลอง `python --version` อีกครั้ง

### Activate ไม่ได้
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Import Error (PyQt6)
```powershell
# ต้อง activate venv ก่อน
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```