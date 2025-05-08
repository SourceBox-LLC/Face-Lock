/**
 * Face Lock Test App - Client-side JavaScript
 * 
 * This script handles the interaction with the Face Lock Server API,
 * including webcam access, face capture, user registration, and authentication.
 */

// Configuration
const API_URL = 'http://localhost:8000'; // Face Lock Server URL
const DEFAULT_SIMILARITY_THRESHOLD = 85.0; // Default face matching threshold

// Global state
let authToken = null;
let currentUser = null;

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show selected tab content
            tabContents.forEach(content => {
                if (content.id === `tab-${tabName}`) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
            
            // Initialize webcam for the active tab
            if (tabName === 'verify') {
                initWebcam('verify-video');
            } else if (tabName === 'register') {
                initWebcam('register-video');
            }
        });
    });
    
    // Initialize webcam for the default tab
    initWebcam('verify-video');
    
    // Button event listeners
    document.getElementById('verify-capture-btn').addEventListener('click', captureAndVerify);
    document.getElementById('register-capture-btn').addEventListener('click', captureAndRegister);
    document.getElementById('list-users-btn').addEventListener('click', listUsers);
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Check server status on load
    checkServerStatus();
});

/**
 * Initialize webcam access for a specific video element
 * @param {string} videoElementId - ID of the video element to display the webcam feed
 */
async function initWebcam(videoElementId) {
    const videoElement = document.getElementById(videoElementId);
    
    try {
        // Stop any existing streams
        if (videoElement.srcObject) {
            videoElement.srcObject.getTracks().forEach(track => track.stop());
        }
        
        // Request camera access
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        });
        
        videoElement.srcObject = stream;
    } catch (error) {
        console.error('Error accessing webcam:', error);
        showError(`Webcam access error: ${error.message}`);
    }
}

/**
 * Check if the Face Lock Server is running
 */
async function checkServerStatus() {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('status-text');
    
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            statusIndicator.classList.remove('offline');
            statusIndicator.classList.add('online');
            statusText.textContent = `Server Status: Online (v${data.version})`;
        } else {
            throw new Error(`Server responded with status: ${response.status}`);
        }
    } catch (error) {
        console.error('Server connection error:', error);
        statusIndicator.classList.remove('online');
        statusIndicator.classList.add('offline');
        statusText.textContent = 'Server Status: Offline (Connection Error)';
    }
}

/**
 * Capture image from webcam and convert to a blob
 * @param {string} videoId - ID of the video element
 * @param {string} canvasId - ID of the canvas element
 * @returns {Blob} - Image blob
 */
function captureImage(videoId, canvasId) {
    const video = document.getElementById(videoId);
    const canvas = document.getElementById(canvasId);
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob
    return new Promise(resolve => {
        canvas.toBlob(blob => {
            resolve(blob);
        }, 'image/jpeg', 0.9);
    });
}

/**
 * Capture a face image and verify it against registered faces
 */
async function captureAndVerify() {
    const resultElement = document.getElementById('verify-result');
    resultElement.className = 'result-message';
    resultElement.textContent = 'Processing...';
    
    try {
        // Capture image from webcam
        const imageBlob = await captureImage('verify-video', 'verify-canvas');
        
        // Create form data
        const formData = new FormData();
        formData.append('face_image', imageBlob, 'face.jpg');
        formData.append('similarity_threshold', DEFAULT_SIMILARITY_THRESHOLD);
        
        // Send verification request
        const response = await fetch(`${API_URL}/verify/`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Store authentication token
            authToken = result.token;
            currentUser = {
                userId: result.user_id,
                similarity: result.similarity,
                authTime: new Date().toLocaleTimeString()
            };
            
            // Show success message
            resultElement.className = 'result-message success';
            resultElement.textContent = `Verification successful! Welcome, ${result.user_id}`;
            
            // Update authenticated section
            document.getElementById('user-id').textContent = result.user_id;
            document.getElementById('user-name').textContent = result.user_id;
            document.getElementById('user-similarity').textContent = `${result.similarity.toFixed(2)}%`;
            document.getElementById('auth-time').textContent = currentUser.authTime;
            
            // Switch to authenticated view
            setTimeout(() => {
                document.getElementById('section-login').classList.remove('active');
                document.getElementById('section-login').classList.add('hidden');
                document.getElementById('section-authenticated').classList.remove('hidden');
                document.getElementById('section-authenticated').classList.add('active');
            }, 1000);
        } else {
            // Show error message
            resultElement.className = 'result-message error';
            resultElement.textContent = `Verification failed: ${result.message}`;
        }
    } catch (error) {
        console.error('Error during verification:', error);
        resultElement.className = 'result-message error';
        resultElement.textContent = `Error: ${error.message}`;
    }
}

/**
 * Capture a face image and register a new user
 */
async function captureAndRegister() {
    const userId = document.getElementById('register-user-id').value.trim();
    const fullName = document.getElementById('register-name').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const resultElement = document.getElementById('register-result');
    
    resultElement.className = 'result-message';
    resultElement.textContent = '';
    
    // Validate user ID
    if (!userId) {
        resultElement.className = 'result-message error';
        resultElement.textContent = 'Please enter a User ID';
        return;
    }
    
    try {
        resultElement.textContent = 'Processing...';
        
        // Capture image from webcam
        const imageBlob = await captureImage('register-video', 'register-canvas');
        
        // Create form data
        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('face_image', imageBlob, 'face.jpg');
        
        if (fullName) {
            formData.append('full_name', fullName);
        }
        
        if (email) {
            formData.append('email', email);
        }
        
        // Send registration request
        const response = await fetch(`${API_URL}/register/`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message
            resultElement.className = 'result-message success';
            resultElement.textContent = `Registration successful! Face ID: ${result.face_id}`;
            
            // Clear form
            document.getElementById('register-user-id').value = '';
            document.getElementById('register-name').value = '';
            document.getElementById('register-email').value = '';
            
            // Switch to verify tab
            setTimeout(() => {
                document.querySelector('[data-tab="verify"]').click();
            }, 2000);
        } else {
            // Show error message
            resultElement.className = 'result-message error';
            resultElement.textContent = `Registration failed: ${result.message}`;
        }
    } catch (error) {
        console.error('Error during registration:', error);
        resultElement.className = 'result-message error';
        resultElement.textContent = `Error: ${error.message}`;
    }
}

/**
 * List all registered users (requires authentication)
 */
async function listUsers() {
    const usersList = document.getElementById('users-list');
    const userListElement = document.getElementById('users');
    
    if (!authToken) {
        showError('Authentication required');
        return;
    }
    
    try {
        // Send request to list users
        const response = await fetch(`${API_URL}/users/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear previous list
            userListElement.innerHTML = '';
            
            // Add users to list
            result.users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = user;
                userListElement.appendChild(li);
            });
            
            // Show users list
            usersList.classList.remove('hidden');
        } else {
            showError(`Failed to list users: ${result.message}`);
        }
    } catch (error) {
        console.error('Error listing users:', error);
        showError(`Error: ${error.message}`);
    }
}

/**
 * Log out the current user
 */
function logout() {
    // Clear authentication
    authToken = null;
    currentUser = null;
    
    // Hide users list
    document.getElementById('users-list').classList.add('hidden');
    
    // Switch back to login view
    document.getElementById('section-authenticated').classList.remove('active');
    document.getElementById('section-authenticated').classList.add('hidden');
    document.getElementById('section-login').classList.remove('hidden');
    document.getElementById('section-login').classList.add('active');
    
    // Reset result messages
    document.getElementById('verify-result').className = 'result-message';
    document.getElementById('verify-result').textContent = '';
    document.getElementById('register-result').className = 'result-message';
    document.getElementById('register-result').textContent = '';
    
    // Reinitialize webcam for verify tab
    initWebcam('verify-video');
}

/**
 * Show an error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    alert(`Error: ${message}`);
}
