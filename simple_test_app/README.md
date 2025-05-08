# Face Lock Server - Simple Test Application

A demonstration web application showing how to integrate facial recognition authentication using the Face Lock Server.

## Overview

This simple test application demonstrates the core functionality of the Face Lock Server through a user-friendly web interface. It provides a complete implementation example that you can use as a reference when integrating facial authentication into your own applications.

## Features

- **User Registration**: Register faces with the Face Lock Server
- **Facial Authentication**: Verify identity through facial recognition
- **JWT Authentication Flow**: Complete client-side token management
- **Protected Content Access**: View content only accessible after authentication
- **User Management**: List registered users and manage accounts

## Application Structure

- `index.html`: Main user interface with webcam integration
- `styles.css`: CSS styling for the application
- `app.js`: JavaScript client that communicates with the Face Lock Server API
- `server.py`: Simple HTTP server to serve the web application

## Running the Application

### Prerequisites

- Face Lock Server running on http://localhost:8000
- Python 3.8+ installed
- Web browser with webcam access

### Steps to Run

1. Ensure the Face Lock Server is running:
   ```bash
   # In the main Face Lock Server directory
   uvicorn app:app --reload
   ```

2. Start the test application:
   ```bash
   # In the simple_test_app directory
   python server.py
   ```

3. The application will automatically open in your default web browser at http://localhost:8080

## How to Use

### Registering a User

1. Click on the "Register Face" tab
2. Enter a unique User ID
3. Optionally enter your full name and email
4. Position your face in the camera view
5. Click "Capture & Register"

### Verifying Identity

1. Click on the "Verify Face" tab (if not already selected)
2. Position your face in the camera view
3. Click "Capture & Verify"
4. Upon successful verification, you'll be authenticated and shown the protected content

### Protected Features

After authentication, you can:
- View your user information
- List all registered users in the system
- Log out to end your session

## Technical Implementation

This application demonstrates several important concepts:

- **Webcam Integration**: Accessing the device camera and capturing images
- **Form Data Management**: Building multipart/form-data requests with images
- **JWT Token Handling**: Storing and using authentication tokens
- **Protected API Calls**: Making authenticated requests
- **User Interface State Management**: Switching between authenticated and non-authenticated views

## Customization

To modify the application:

- Change `API_URL` in `app.js` if your Face Lock Server is running on a different URL
- Adjust `DEFAULT_SIMILARITY_THRESHOLD` for more or less strict face matching
- Modify the UI in `index.html` and `styles.css` to match your application's design

## Troubleshooting

- **Camera Access Issues**: Make sure your browser has permission to access your camera
- **Connection Errors**: Verify that the Face Lock Server is running
- **Authentication Failures**: Try adjusting the lighting or positioning for better facial recognition
- **CORS Issues**: Ensure the Face Lock Server has CORS properly configured

## Learn More

For more information on the Face Lock Server API and implementation details, refer to the main [Face Lock Server README](../README.md).
