def process_with_assistant(self, client, text):
    """Process text using OpenAI Assistant API"""
    try:
        # Create a thread for the conversation
        thread = client.beta.threads.create()
        
        # Add the user message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=text
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.openai_assistant_id
        )
        
        # Wait for the run to complete
        import time
        while run.status in ['queued', 'in_progress']:
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            # Get the assistant's response
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            
            # Get the latest assistant message
            for message in messages.data:
                if message.role == 'assistant':
                    response_text = message.content[0].text.value
                    self.get_logger().info(f'OpenAI Assistant response: {response_text}')
                    
                    # Parse JSON response and extract only the "answer" field
                    parsed_response = self.parse_assistant_response(response_text)
                    return parsed_response