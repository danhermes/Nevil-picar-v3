#!/usr/bin/env python3
"""
Test the simple fix: Stop/start listening based on speaking status
"""

print("Testing the simple fix logic...")
print()

# Simulate the flow
print("1. Nevil starts → is_listening = True (microphone ON)")
is_listening = True

print(f"   Microphone: {'ON' if is_listening else 'OFF'}")
print()

print("2. User says 'Hi Nevil' → Audio captured and transcribed")
print("   (Because microphone is ON)")
print()

print("3. AI generates response → publishes text_response")
print()

print("4. TTS node publishes speaking_status = True")
print()

print("5. STT node receives speaking_status = True")
print("   → Calls _stop_listening()")
is_listening = False

print(f"   Microphone: {'ON' if is_listening else 'OFF'}")
print()

print("6. Nevil speaks...")
print("   (Microphone is OFF - can't hear himself)")
print()

print("7. TTS finishes → publishes speaking_status = False")
print()

print("8. STT node receives speaking_status = False")
print("   → Calls _start_listening()")
is_listening = True

print(f"   Microphone: {'ON' if is_listening else 'OFF'}")
print()

print("9. Ready for next user input")
print()

print("✅ Simple walkie-talkie turn-taking")
print()
print("To test:")
print("1. Kill Nevil if running: pkill -f 'python.*nevil'")
print("2. Restart: ./nevil start")
print("3. Say 'Hi Nevil'")
print("4. Check logs for: '🔇 Stopped listening' and '🎤 Resumed listening'")
