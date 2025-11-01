# iOS Shortcut Configuration Guide

Complete guide to setting up iPhone shortcuts for capturing and submitting research ideas to your Research Swarm system.

## Prerequisites

- iPhone with iOS 14 or later
- Shortcuts app installed (pre-installed on iOS)
- Research Swarm API running and accessible
- (Recommended) Tailscale installed for secure access

## Option 1: Basic Local Network Shortcut

Perfect for when you're on the same WiFi network as your server.

### Setup Steps

1. **Open Shortcuts App**
   - Launch the Shortcuts app on your iPhone

2. **Create New Shortcut**
   - Tap the "+" button in the top right
   - Name it "Research Idea"

3. **Add Actions**

   **Action 1: Get Input**
   - Search for "Ask for Input"
   - Add the action
   - Configure:
     - Question: "What's your research idea?"
     - Input Type: Text
     - Default Answer: (leave empty)

   **Action 2: Make API Request**
   - Search for "Get Contents of URL"
   - Add the action
   - Configure:
     - URL: `http://YOUR_SERVER_IP:8000/api/v1/ideas`
     - Method: POST
     - Headers:
       - Add Header
       - Key: `Content-Type`
       - Value: `application/json`
     - Request Body: JSON
       ```json
       {
         "idea": "SHORTCUT_INPUT",
         "priority": "medium"
       }
       ```
     - Note: Tap "Shortcut Input" from the variables menu to insert the question response

   **Action 3: Parse Response**
   - Search for "Get Dictionary Value"
   - Add the action
   - Configure:
     - Dictionary: "Contents of URL"
     - Key: "idea_id"

   **Action 4: Show Notification**
   - Search for "Show Notification"
   - Add the action
   - Configure:
     - Title: "Idea Submitted! ✅"
     - Body: Tap to insert "Dictionary Value" variable
     - Sound: Choose your preference
     - Show when running: ON

4. **Test the Shortcut**
   - Tap the play button
   - Enter a test idea
   - Verify you receive a notification with the idea ID

### Find Your Server IP

On your Mac/Linux server:
```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'
```

## Option 2: Secure Remote Access with Tailscale (Recommended)

This allows you to submit ideas from anywhere with an internet connection.

### Setup Tailscale

1. **Install Tailscale on Server**
   ```bash
   # macOS
   brew install tailscale

   # Linux
   curl -fsSL https://tailscale.com/install.sh | sh
   ```

2. **Start Tailscale**
   ```bash
   sudo tailscale up
   ```

3. **Get Your Tailscale IP**
   ```bash
   tailscale ip -4
   # Example output: 100.101.102.103
   ```

4. **Install Tailscale on iPhone**
   - Download from App Store
   - Sign in with same account
   - Enable VPN

5. **Update Shortcut URL**
   - Edit your shortcut
   - Change URL to: `http://100.x.x.x:8000/api/v1/ideas`
   - Replace with your Tailscale IP

### Benefits of Tailscale
- Encrypted communication
- Works from anywhere
- No port forwarding needed
- No public IP exposure
- Free for personal use

## Option 3: Advanced Shortcut with Status Checking

This version submits the idea and then checks its status.

### Additional Actions

After the notification action, add:

**Action 5: Wait**
- Search for "Wait"
- Set to 2 seconds

**Action 6: Check Status**
- Search for "Get Contents of URL"
- Configure:
  - URL: Combine text `http://YOUR_IP:8000/api/v1/ideas/` + "Dictionary Value" (idea_id) + `/status`
  - Method: GET

**Action 7: Parse Status**
- Search for "Get Dictionary Value"
- Key: "status"

**Action 8: Show Status**
- Search for "Show Notification"
- Title: "Processing Status"
- Body: "Dictionary Value" (status)

## Trigger Options

### 1. Back Tap Trigger

**Setup:**
1. Settings → Accessibility → Touch
2. Scroll to "Back Tap"
3. Choose Double Tap or Triple Tap
4. Select your "Research Idea" shortcut

**Usage:** Tap the back of your iPhone 2-3 times to trigger

### 2. Home Screen Widget

**Setup:**
1. Long press home screen
2. Tap "+" in top left
3. Search for "Shortcuts"
4. Choose widget size
5. Add to home screen
6. Long press widget → Edit Widget
7. Select "Research Idea" shortcut

**Usage:** Tap the widget on your home screen

### 3. Siri Voice Command

**Setup:**
1. Open shortcut settings (tap ⓘ button)
2. Tap "Add to Siri"
3. Record phrase: "Research this idea" or "Capture idea"

**Usage:** Say "Hey Siri, research this idea"

### 4. Lock Screen Widget (iOS 16+)

**Setup:**
1. Long press lock screen
2. Tap "Customize"
3. Tap widget area
4. Add Shortcuts widget
5. Select "Research Idea"

**Usage:** Launch from lock screen

### 5. Action Button (iPhone 15 Pro)

**Setup:**
1. Settings → Action Button
2. Choose "Shortcut"
3. Select "Research Idea"

**Usage:** Press and hold Action button

## Advanced Features

### Add Context Field

Modify the shortcut to capture additional context:

1. Add another "Ask for Input" before the API request
   - Question: "Any additional context? (Optional)"

2. Update the JSON body:
   ```json
   {
     "idea": "FIRST_INPUT",
     "context": "SECOND_INPUT",
     "priority": "medium"
   }
   ```

### Priority Selection

Add a menu to choose priority:

1. After first input, add "Choose from Menu"
2. Options: Low, Medium, High, Urgent
3. Each option sets a different priority value
4. Update JSON accordingly

### Voice Input

Replace "Ask for Input" with "Dictate Text":
- Automatically converts speech to text
- No typing required
- Perfect for truly spontaneous ideas

### Share Sheet Integration

Make it available from any app:

1. Shortcut Settings → Details
2. Enable "Show in Share Sheet"
3. Accept: Text, URLs, Safari Web Pages

**Usage:** In any app, tap Share → Research Idea

## Complete Shortcut Template

Here's the JSON representation you can import:

```json
{
  "name": "Research Idea",
  "actions": [
    {
      "type": "askForInput",
      "question": "What's your research idea?",
      "inputType": "text"
    },
    {
      "type": "getUrl",
      "url": "http://YOUR_SERVER:8000/api/v1/ideas",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "idea": "{{input}}",
        "priority": "medium"
      }
    },
    {
      "type": "getDictionaryValue",
      "key": "idea_id"
    },
    {
      "type": "showNotification",
      "title": "Idea Submitted! ✅",
      "body": "ID: {{dictionaryValue}}"
    }
  ]
}
```

## Troubleshooting

### Connection Failed

**Check:**
1. Server is running: `curl http://YOUR_IP:8000/health`
2. iPhone is on same network (or Tailscale connected)
3. URL in shortcut is correct
4. Server firewall allows port 8000

**Fix:**
```bash
# Check API is running
ps aux | grep uvicorn

# Test from terminal
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "test"}'
```

### Authentication Error

If you've added authentication:
1. Add Authorization header
2. Key: `Authorization`
3. Value: `Bearer YOUR_TOKEN`

### SSL/HTTPS Issues

For production with SSL:
1. Use `https://` instead of `http://`
2. Ensure certificate is valid
3. iOS may require certificate trust

### Timeout Issues

If requests timeout:
1. Increase timeout in shortcut settings
2. Check server response time
3. Verify network connectivity

## Example Usage Scenarios

### Morning Commute
- "Hey Siri, research this idea"
- Dictate idea while driving
- Review results when you arrive

### During Exercise
- Double-tap back of iPhone
- Quick voice capture
- Continue your workout

### Night Time Ideas
- Use lock screen widget
- Capture before you forget
- No need to unlock phone

### Reading Articles
- Select text in Safari
- Share → Research Idea
- Automatically captures article + your thoughts

## Privacy & Security

### Best Practices

1. **Use Tailscale** for remote access
2. **Don't expose** API to public internet without authentication
3. **Review** submitted ideas periodically
4. **Backup** your research repository
5. **Limit** API access to your devices only

### Tailscale ACL Example

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:mobile"],
      "dst": ["tag:research-server:8000"]
    }
  ],
  "tagOwners": {
    "tag:mobile": ["your-email@example.com"],
    "tag:research-server": ["your-email@example.com"]
  }
}
```

## Next Steps

1. ✅ Set up basic shortcut
2. ✅ Test with sample idea
3. ✅ Configure favorite trigger (Back Tap recommended)
4. ✅ Set up Tailscale for remote access
5. ✅ Customize for your workflow
6. ✅ Share with team members (optional)

## Real-World Tips

### Capture Everything
- No idea is too small
- Let the system evaluate feasibility
- Review and refine later

### Use Consistent Triggers
- Pick one trigger and stick with it
- Muscle memory makes it effortless
- Back Tap is fastest in practice

### Voice vs. Text
- Voice: Better for spontaneous, on-the-go
- Text: Better for detailed, considered ideas
- Mix both based on situation

### Review Cadence
- Daily: Quick scan of submitted ideas
- Weekly: Deep dive into research results
- Monthly: Implement top ideas

## Support

If you encounter issues:
1. Check server logs: `tail -f logs/research-swarm.log`
2. Test API directly with curl
3. Verify Shortcuts has network permissions
4. Check iOS system logs in Console app (Mac)

Happy idea capturing! 💡
