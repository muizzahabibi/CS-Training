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

    def generate_message(self, messages, max_tokens):
        try:
            system_content = [
                {
                    "type": "text",
                    "text": self.perannya,
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

    def process_user_input(self, user_input):
        self.session_state.messages.append({"role": "user", "content": user_input})

        response_message = self.generate_message(
            messages=self.session_state.messages,
            max_tokens=2048)

        if "error" in response_message:
            return f"An error occurred: {response_message['error']}"

        follow_up_response = self.generate_message(
            messages=self.session_state.messages,
            max_tokens=2048,
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
    messages_json = json.dumps(st.session_state["messages"][2:], indent=4)

    # Convert JSON string to bytes for download
    json_bytes = messages_json.encode('utf-8')

    # Provide download button for the JSON file
    st.download_button(
        label="Download History",
        data=json_bytes,
        file_name=f"messages_{save_title}.json",
        mime="application/json"
    )
    st.success(f"Sukses backup chat: *messages_{save_title}.json*")

# Fungsi untuk membuat kunci dari password
def derive_key_from_password(password: str, salt: bytes) -> bytes:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    import base64
    
    # Menggunakan hashes.SHA256() sebagai algoritma hash
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),  # Menggunakan objek SHA256
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

# Fungsi untuk mendekripsi API key
def decrypt_api_key(encrypted_api_key: bytes, password: str, salt: bytes) -> str:
    from cryptography.fernet import Fernet
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_api_key).decode()

def main():
    encrypted_api_key = b'gAAAAABm61o_UvG_BNFpe-5pSykVmGCu_9e8pXtYkjYPAM5lU_4aw4kIoGXqpSj_En59OCCAFJ3UQ5fD3Z518uE74aS5I84b7L8qFykGC3BlG_PtKwk-120OUwVpH-CVcLkxxcz0fm3C0EwhrYiNBWkpsQ3w4FfKdK-dLjT_91TSwqj_TYKyahCirK4eVF69wAVnEjaWib2CuNntY6W_Eqm4Qp4s7i1-cQ=='
    salt = b'\xb9\xe1z\xed\xfd\x84GF>w\x9c\xe6\xfd\x17\r\x14'


    if st.button("Save History"):
        save_history()

    dl = st.empty()
    st.title("Chat with Habibi, Raga Pool Assistant🤖")

    radio_input_container = st.empty()
    text_input_container = st.empty()

    peran = radio_input_container.radio("Pilih peran yang akan dijalani oleh AI",["Sales","Sales Manager","Customer"]) 
    passwrd = text_input_container.text_input("Masukan passwordnya :", placeholder="***", type="password")
    
    api_k = ""

    try:
        # Dekripsi API key
        api_k = decrypt_api_key(encrypted_api_key, passwrd, salt)
        
    except Exception as e:
        st.warning("Mohon masukan password yang benar", icon="⚠️")

    

    if api_k:
        roles = {
            "Sales": SALES,
            "Sales Manager": SALES_MANAGER,
            "Customer": CUSTOMER
        }

        prn = roles.get(peran)  # default to SALES
        st.write(f"Peran yang dipilih: {peran}")

        text_input_container.empty()
        radio_input_container.empty()

        if "messages" not in st.session_state:
            if peran == "Customer" :
                st.session_state.messages = [
                    {'role': "user", "content": "Halo, kamu sebagai calon customer raga pool akan bertanya, saya akan menjawab"},
                    {'role': "assistant", "content": "Understood"},
                ]
            elif peran == "Sales Manager":
                st.session_state.messages = [
                    {'role': "user", "content": "Halo, kamu sebagai sales manager, akan memberikan koreksi / masukan / analisa terhadap history chat yang akan saya berikan"},
                    {'role': "assistant", "content": "Understood"},
                ]
            else:
                st.session_state.messages = [
                    {'role': "user", "content": "Halo"},
                    {'role': "assistant", "content": "Understood"},
                ]

        chatbot = ChatBot(st.session_state, api_k, prn)

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
