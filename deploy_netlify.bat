@echo off
REM Netlify Deployment Script for Windows
REM This script helps you deploy the dashboard to Netlify

echo.
echo 🚀 Netlify Deployment Helper
echo ==============================
echo.
echo Choose deployment method:
echo 1. Deploy via Netlify CLI (requires netlify-cli installed)
echo 2. Show manual deployment instructions
echo 3. Create deployment package (zip file)
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo 📦 Deploying via Netlify CLI...
    where netlify >nul 2>&1
    if errorlevel 1 (
        echo ❌ Netlify CLI not found. Install it with: npm install -g netlify-cli
        exit /b 1
    )
    
    echo Checking if logged in...
    netlify status || netlify login
    
    echo.
    echo Initializing deployment...
    netlify deploy --prod
    goto :end
)

if "%choice%"=="2" (
    echo.
    echo 📋 Manual Deployment Instructions:
    echo ====================================
    echo.
    echo 1. Go to https://app.netlify.com
    echo 2. Click 'Add new site' → 'Deploy manually'
    echo 3. Drag and drop your project folder
    echo 4. Make sure these files are included:
    echo    - horeca_optimized_dashboard.html
    echo    - dashboard_data.json
    echo    - netlify.toml
    echo    - _redirects
    echo.
    echo Or zip the folder and upload the zip file.
    goto :end
)

if "%choice%"=="3" (
    echo.
    echo 📦 Creating deployment package...
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set ZIP_NAME=horeca-dashboard-%datetime:~0,8%-%datetime:~8,6%.zip
    
    REM Create zip with required files (requires PowerShell or 7-Zip)
    powershell -command "Compress-Archive -Path horeca_optimized_dashboard.html,dashboard_data.json,netlify.toml,_redirects,README_NETLIFY.md -DestinationPath %ZIP_NAME% -Force" 2>nul
    
    if exist "%ZIP_NAME%" (
        echo ✅ Package created: %ZIP_NAME%
        echo    Upload this file to Netlify via their dashboard
    ) else (
        echo ❌ Failed to create package. Make sure PowerShell is available.
        echo    You can manually zip these files:
        echo    - horeca_optimized_dashboard.html
        echo    - dashboard_data.json
        echo    - netlify.toml
        echo    - _redirects
        echo    - README_NETLIFY.md
    )
    goto :end
)

echo Invalid choice
exit /b 1

:end
echo.
echo ✅ Done!
pause

