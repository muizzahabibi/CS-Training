from anthropic import Anthropic
from config import SALES, SALES_MANAGER, CUSTOMER, TASK_SPECIFIC_INSTRUCTIONS
from dotenv import load_dotenv
import streamlit as st
import time, json

load_dotenv()

class ChatBot:
    def __init__(self, session_state, api_k,peran):
        self.anthropic = Anthropic(api_key=api_k)
        self.session_state = session_state
        self.perannya = peran

    def generate_message(self, messages, max_tokens, perannya):
        try:
            system_content = [
                {
                    "type": "text",
                    "text": perannya,
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": TASK_SPECIFIC_INSTRUCTIONS,
                    "cache_control": {"type": "ephemeral"}
                }
            ]

            response = self.anthropic.beta.prompt_caching.messages.create(
                model="claude-3-5-sonnet-20240620",
                system=system_content,
                max_tokens=max_tokens,
                messages=messages,
                extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def process_user_input(self, user_input, perannya):
        self.session_state.messages.append({"role": "user", "content": user_input})

        response_message = self.generate_message(
            messages=self.session_state.messages,
            max_tokens=2048,
            perannya,
        )

        if "error" in response_message:
            return f"An error occurred: {response_message['error']}"

        follow_up_response = self.generate_message(
            messages=self.session_state.messages,
            max_tokens=2048,
            perannya,
        )

        if "error" in follow_up_response:
            return f"An error occurred: {follow_up_response['error']}"

        response_text = follow_up_response.content[0].text
        self.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )
        return response_text

        if response_message.content[0].type == "text":
            response_text = response_message.content[0].text
            self.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )
            return response_text
        else:
            raise Exception("An error occurred: Unexpected response type")


def save_history():
	 """
	 Save the history messages and provide a download link.
	 """
	 if not st.session_state.messages:
		  st.info("No Messages", icon="ℹ️")
		  st.stop()

	 # Generate save title
	 save_title = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
	 messages_json = json.dumps(st.session_state["messages"][2:])

	 # Save the JSON string to a file
	 filename = f"backup/messages_{save_title}.json"
	 with open(filename, "w") as file:
		  file.write(messages_json)
	 
	 # Provide download link
	 # file_link = f"[Download History](./{filename})"
	 st.markdown(f"_Sukses backup chat : *{filename}*_", unsafe_allow_html=True)

def main():
    # download_button = st.button("Download History", on_click=save_history)
    st.title("Chat with Habibi, Raga Pool Assistant🤖")

    radio_input_container = st.empty()
    text_input_container = st.empty()

    peran = radio_input_container.radio("Pilih peran yang akan dijalani oleh AI",["SALES","SALES_MANAGER","CUSTOMER"]) 
    user_claude_api_key = text_input_container.text_input("Enter your Anthropic API Key:", placeholder="sk-...", type="password")
    if user_claude_api_key:
        api_k = user_claude_api_key
    else:
        st.warning("Please enter your Anthropic Claude API key", icon="⚠️")

    if user_claude_api_key:
        text_input_container.empty()
        radio_input_container.empty()

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {'role': "user", "content": "Halo Raga Pool"},
                {'role': "assistant", "content": "Understood"},
            ]

        chatbot = ChatBot(st.session_state, api_k, peran)

        # Display user and assistant messages skipping the first two
        for message in st.session_state.messages[2:]:
            # ignore tool use blocks
            if isinstance(message["content"], str):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if user_msg := st.chat_input("Type your message here..."):
            st.chat_message("user").markdown(user_msg)

            with st.chat_message("assistant"):
                with st.spinner("Habibi mengetik..."):
                    response_placeholder = st.empty()
                    full_response = chatbot.process_user_input(user_msg)
                    response_placeholder.markdown(full_response)


if __name__ == "__main__":
	main()
