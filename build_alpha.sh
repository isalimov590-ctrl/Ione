#!/bin/bash

echo "Starting Ione Alpha Build Process..."

# Install necessary tools
pip install flet fastapi uvicorn websockets requests pydantic python-multipart

# Build for different platforms
echo "Building for Android (APK)..."
flet build apk

echo "Building for Windows..."
flet build windows

echo "Building for Linux..."
flet build linux

echo "Builds complete! Check the 'build/' directory for assets."
