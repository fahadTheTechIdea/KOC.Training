# How to Publish Projects to Community

This guide explains how to use the "Publish to Community" feature in MLStudio to share your trained models with the Community platform.

## Prerequisites

1. **MLStudio** must be running and connected to **Community**
2. You must have a **trained model** in a project
3. You must be **logged in** to both applications
4. **Community connection** must be configured in MLStudio settings

## Step 1: Configure Community Connection

1. **Open MLStudio** and go to **Settings**
2. **Navigate to "Community Platform Connection"** section
3. **Enter the Community URL**:
   - Local: `http://localhost:5001`
   - Production: `https://your-community-domain.com`
4. **Enter API Key** (if required by your Community instance)
5. **Click "Test Connection"** to verify
6. **Click "Save"** to store the configuration

## Step 2: Open Your Project

1. **Navigate to Projects** in MLStudio
2. **Click on the project** that contains your trained model
3. Ensure the project has:
   - A trained model file (`.pkl`, `.h5`, `.joblib`, etc.)
   - Completed experiments with good results

## Step 3: Publish to Community

1. **Click the "Publish to Community" button** in the project detail page
2. **A modal will open** with the following options:
   - **Select Competition**: Choose an active competition from the Community platform
   - **Submission Name**: Enter a name for your submission
   - **Description**: Add a description of your model and approach
   - **Model File**: Select the trained model file to upload

3. **Fill in the required information**:
   - Select a competition from the dropdown
   - Enter a descriptive submission name
   - Write a clear description of your model
   - Choose the model file to submit

4. **Click "Publish to Community"** button in the modal

## Step 4: Verify Publication

1. **Check the success message** that appears after publishing
2. **Navigate to Community** platform
3. **Go to the selected competition**
4. **Check the leaderboard** to see your submission
5. **View your submission details** in the competition page

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to Community"
- **Solution**: 
  - Verify Community URL is correct
  - Check that Community is running
  - Ensure network connectivity
  - Test connection in Settings

### No Competitions Available

**Problem**: Competition dropdown is empty
- **Solution**:
  - Ensure there are active competitions in Community
  - Check that you're logged in to Community
  - Verify API permissions

### Model File Not Found

**Problem**: "Model file not found" error
- **Solution**:
  - Ensure the model has been trained and saved
  - Check the model file path is correct
  - Verify file permissions

### Authentication Errors

**Problem**: "Unauthorized" or "Authentication failed"
- **Solution**:
  - Log in to both MLStudio and Community
  - Check JWT tokens are valid
  - Re-authenticate if needed

## Best Practices

1. **Test Locally First**: Test your model thoroughly before publishing
2. **Write Clear Descriptions**: Help others understand your approach
3. **Document Your Model**: Include information about:
   - Features used
   - Preprocessing steps
   - Model architecture
   - Training parameters
   - Performance metrics

4. **Follow Competition Rules**: Ensure your submission meets competition requirements
5. **Version Control**: Keep track of different model versions you submit

## Alternative: Manual Upload

If the automatic publish feature doesn't work:

1. **Export your model** from MLStudio
2. **Log in to Community**
3. **Navigate to the competition**
4. **Use the "Submit" button** in the competition page
5. **Upload your model file manually**

## API Integration

For programmatic publishing, you can use the Community API:

```python
import requests

# Authenticate
response = requests.post('http://localhost:5001/api/v1/auth/login', json={
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['access_token']

# Publish model
headers = {'Authorization': f'Bearer {token}'}
files = {'model_file': open('model.pkl', 'rb')}
data = {
    'competition_id': 1,
    'name': 'My Model Submission',
    'description': 'Model description'
}

response = requests.post(
    'http://localhost:5001/api/v1/competitions/1/submissions',
    headers=headers,
    files=files,
    data=data
)
```

## Support

For issues with publishing:
1. Check the browser console for JavaScript errors
2. Review MLStudio logs for backend errors
3. Verify Community API is accessible
4. Check network connectivity between applications

