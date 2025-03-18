#!/bin/bash

# Exit on error
set -e

# Configuration
APP_DIR="/var/www/saieed-clinical-lab"
REPO_URL="https://github.com/zub165/saieed-clinical-lab.git"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="saieed-lab"

echo "Starting deployment..."

# Create application directory if it doesn't exist
sudo mkdir -p $APP_DIR

# Set proper ownership
sudo chown www-data:www-data $APP_DIR

# Clone or update repository
if [ -d "$APP_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd $APP_DIR
    sudo -u www-data git pull origin main
else
    echo "Cloning repository..."
    sudo -u www-data git clone $REPO_URL $APP_DIR
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    cd $APP_DIR
    sudo -u www-data python3 -m venv $VENV_DIR
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
sudo -u www-data $VENV_DIR/bin/pip install -r $APP_DIR/requirements.txt

# Create .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating .env file..."
    sudo -u www-data cp $APP_DIR/.env.example $APP_DIR/.env
    echo "Please update the .env file with your production settings"
fi

# Copy systemd service file
echo "Setting up systemd service..."
sudo cp $APP_DIR/saieed-lab.service /etc/systemd/system/
sudo systemctl daemon-reload

# Create temp directory for PDF generation
echo "Creating temp directory..."
sudo -u www-data mkdir -p $APP_DIR/temp

# Initialize database if it doesn't exist
if [ ! -f "$APP_DIR/saieed_lab.db" ]; then
    echo "Initializing database..."
    cd $APP_DIR
    sudo -u www-data $VENV_DIR/bin/python init_db.py
fi

# Restart service
echo "Restarting service..."
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

echo "Deployment completed successfully!"
echo "Please check the service status with: sudo systemctl status $SERVICE_NAME" 