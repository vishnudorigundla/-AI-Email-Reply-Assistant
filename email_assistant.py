import streamlit as st
import os
import re
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
import io
import docx
import email
from email import policy

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_email(email_content):
    """
    Analyze incoming email to understand context and intent in both English and Telugu
    """
    try:
        prompt = f"""
        Analyze the following email and provide analysis in both English and Telugu languages:
        
        Email content:
        {email_content}
        
        Please provide the analysis in this exact format:
        
        ## English Analysis
        **Summary:** [brief summary in English, 2-3 sentences]
        **Intent:** [sender's intent/purpose in English]
        **Key Points:** [bullet points in English]
        **Urgency:** [Low/Medium/High]
        
        ## Telugu Analysis / తెలుగు విశ్లేషణ
        **సారాంశం:** [brief summary in Telugu, 2-3 sentences]
        **ఉద్దేశ్యం:** [sender's intent/purpose in Telugu]
        **ముఖ్య అంశాలు:** [bullet points in Telugu]
        **అత్యవసరత:** [తక్కువ/మధ్యమ/అధిక]
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "Unable to analyze email."
    except Exception as e:
        return f"Error analyzing email: {str(e)}"

def generate_email_reply(email_content, tone="professional", length="medium", action_type=None, custom_signature=""):
    """
    Generate AI-powered email reply with specified tone and length
    """
    try:
        # Define tone characteristics
        tone_instructions = {
            "professional": "Use formal business language, be respectful and direct",
            "friendly": "Use warm, approachable language while maintaining professionalism",
            "casual": "Use relaxed, conversational tone but still appropriate for business",
            "formal": "Use very formal, traditional business language with proper etiquette",
            "empathetic": "Show understanding and compassion, acknowledge concerns warmly",
            "assertive": "Be confident and clear, take charge of the situation"
        }
        
        # Define length guidelines
        length_instructions = {
            "short": "Keep the reply to 2-3 sentences maximum, be very concise",
            "medium": "Write a balanced reply of 1-2 paragraphs",
            "detailed": "Provide a comprehensive response with detailed explanations"
        }
        
        # Quick action prompts
        action_prompts = {
            "accept_meeting": "Accept the meeting invitation graciously and confirm availability",
            "decline_politely": "Politely decline the request with a brief explanation",
            "request_info": "Ask for additional information or clarification professionally",
            "acknowledge": "Acknowledge receipt and provide appropriate response",
            "schedule_followup": "Suggest scheduling a follow-up meeting or call"
        }
        
        base_prompt = f"""
        Write a professional email reply to the following email. 
        
        TONE: {tone_instructions.get(tone, tone_instructions['professional'])}
        LENGTH: {length_instructions.get(length, length_instructions['medium'])}
        """
        
        if action_type and action_type in action_prompts:
            base_prompt += f"\nSPECIFIC ACTION: {action_prompts[action_type]}"
        
        base_prompt += f"""
        
        Original email to reply to:
        {email_content}
        
        Generate a complete email reply with:
        - Appropriate subject line (if needed)
        - Professional greeting
        - Main body addressing the sender's points
        - Appropriate closing
        
        Do not include sender's signature - that will be added separately.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=base_prompt
        )
        
        reply_text = response.text if response.text else "Unable to generate reply."
        
        # Add custom signature if provided
        if custom_signature.strip():
            reply_text += f"\n\n{custom_signature}"
        
        return reply_text
    except Exception as e:
        return f"Error generating reply: {str(e)}"

def extract_text_from_docx(file_bytes):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        return f"Error reading DOCX file: {str(e)}"

def extract_text_from_eml(file_bytes):
    """Extract text from EML file"""
    try:
        msg = email.message_from_bytes(file_bytes, policy=policy.default)
        
        # Get email metadata
        subject = msg.get('Subject', 'No Subject')
        sender = msg.get('From', 'Unknown Sender')
        date = msg.get('Date', 'No Date')
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        formatted_email = f"From: {sender}\nSubject: {subject}\nDate: {date}\n\n{body}"
        return formatted_email
    except Exception as e:
        return f"Error reading EML file: {str(e)}"

def main():
    # Page configuration
    st.set_page_config(
        page_title="AI Email Reply Assistant",
        page_icon="✉️",
        layout="wide"
    )
    
    # Main title and description
    st.title("✉️ AI Email Reply Assistant")
    st.markdown("Paste emails and get professional AI-drafted replies instantly with customizable tones and styles.")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Reply Settings")
        
        # Tone selector
        tone = st.selectbox(
            "Select Reply Tone:",
            ["professional", "friendly", "casual", "formal", "empathetic", "assertive"],
            index=0
        )
        
        # Length selector
        length = st.selectbox(
            "Reply Length:",
            ["short", "medium", "detailed"],
            index=1
        )
        
        # Number of drafts
        num_drafts = st.slider("Number of Draft Replies:", 1, 3, 2)
        
        st.markdown("---")
        
        # Custom signature
        st.subheader("📝 Custom Signature")
        custom_signature = st.text_area(
            "Your Signature:",
            placeholder="Best regards,\nJohn Smith\nSenior Manager\ncompany@email.com\n+1-234-567-8900",
            height=100
        )
        
        st.markdown("---")
        st.markdown("### 💡 Quick Tips")
        st.info("""
        - Upload .eml, .txt, or .docx files
        - Try different tones for different scenarios
        - Use quick action buttons for common responses
        - Edit drafts before copying
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📧 Email Input")
        
        # Input method tabs
        input_tab1, input_tab2 = st.tabs(["📝 Paste Email", "📎 Upload File"])
        
        email_content = ""
        
        with input_tab1:
            email_content = st.text_area(
                "Paste your email here:",
                placeholder="Paste the email you want to reply to...",
                height=300,
                help="Copy and paste the email content you need to reply to"
            )
        
        with input_tab2:
            uploaded_file = st.file_uploader(
                "Upload email file:",
                type=['txt', 'eml', 'docx'],
                help="Upload .txt, .eml, or .docx files containing the email"
            )
            
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                
                if uploaded_file.type == "text/plain":
                    email_content = str(file_bytes, 'utf-8')
                elif uploaded_file.name.endswith('.eml'):
                    email_content = extract_text_from_eml(file_bytes)
                elif uploaded_file.name.endswith('.docx'):
                    email_content = extract_text_from_docx(file_bytes)
                
                if email_content:
                    st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
                    with st.expander("📋 Preview loaded content"):
                        st.text_area("Loaded email content:", email_content, height=200, disabled=True)
    
    with col2:
        st.header("🔍 Email Analysis")
        
        if email_content.strip():
            with st.spinner("Analyzing email..."):
                analysis = analyze_email(email_content)
            
            st.markdown("### 📊 Analysis Results")
            st.markdown(analysis)
        else:
            st.info("👆 Paste or upload an email to see analysis")
    
    # Quick Action Buttons
    if email_content.strip():
        st.markdown("---")
        st.subheader("⚡ Quick Actions")
        
        col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns(5)
        
        with col_btn1:
            accept_meeting = st.button("✅ Accept Meeting", use_container_width=True)
        with col_btn2:
            decline_politely = st.button("❌ Decline Politely", use_container_width=True)
        with col_btn3:
            request_info = st.button("❓ Request Info", use_container_width=True)
        with col_btn4:
            acknowledge = st.button("👍 Acknowledge", use_container_width=True)
        with col_btn5:
            schedule_followup = st.button("📅 Schedule Follow-up", use_container_width=True)
        
        # Generate replies button
        st.markdown("---")
        generate_button = st.button("🚀 Generate Reply Drafts", type="primary", use_container_width=True)
        
        # Determine action type based on quick action buttons
        action_type = None
        if accept_meeting:
            action_type = "accept_meeting"
            generate_button = True
        elif decline_politely:
            action_type = "decline_politely"
            generate_button = True
        elif request_info:
            action_type = "request_info"
            generate_button = True
        elif acknowledge:
            action_type = "acknowledge"
            generate_button = True
        elif schedule_followup:
            action_type = "schedule_followup"
            generate_button = True
        
        # Generate and display replies
        if generate_button:
            st.markdown("---")
            st.header("📝 Generated Reply Drafts")
            
            # Generate multiple drafts
            drafts = []
            with st.spinner(f"Generating {num_drafts} reply draft(s)..."):
                for i in range(num_drafts):
                    # Add slight variation for multiple drafts
                    variation_prompt = f" (Draft {i+1} variation)" if num_drafts > 1 else ""
                    reply = generate_email_reply(
                        email_content + variation_prompt, 
                        tone, 
                        length, 
                        action_type, 
                        custom_signature
                    )
                    drafts.append(reply)
            
            # Display drafts in tabs or columns
            if num_drafts == 1:
                st.subheader("📄 Reply Draft")
                st.text_area("Generated Reply:", drafts[0], height=300, key="draft_1")
                st.button(f"📋 Copy Draft to Clipboard", key="copy_1")
                
            else:
                # Create tabs for multiple drafts
                tab_names = [f"📄 Draft {i+1}" for i in range(num_drafts)]
                tabs = st.tabs(tab_names)
                
                for i, tab in enumerate(tabs):
                    with tab:
                        st.text_area(f"Reply Draft {i+1}:", drafts[i], height=300, key=f"draft_{i+1}")
                        col_copy, col_edit = st.columns(2)
                        with col_copy:
                            st.button(f"📋 Copy Draft {i+1}", key=f"copy_{i+1}")
                        with col_edit:
                            if st.button(f"✏️ Edit Draft {i+1}", key=f"edit_{i+1}"):
                                st.session_state[f"edit_mode_{i+1}"] = True
                        
                        # Edit mode
                        if st.session_state.get(f"edit_mode_{i+1}", False):
                            edited_draft = st.text_area(
                                f"Edit Draft {i+1}:", 
                                drafts[i], 
                                height=300, 
                                key=f"edited_draft_{i+1}"
                            )
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button(f"💾 Save Changes", key=f"save_{i+1}"):
                                    drafts[i] = edited_draft
                                    st.session_state[f"edit_mode_{i+1}"] = False
                                    st.success("Changes saved!")
                                    st.rerun()
                            with col_cancel:
                                if st.button(f"❌ Cancel", key=f"cancel_{i+1}"):
                                    st.session_state[f"edit_mode_{i+1}"] = False
                                    st.rerun()
            
            # Additional options
            st.markdown("---")
            st.subheader("📋 Additional Options")
            
            col_opt1, col_opt2, col_opt3 = st.columns(3)
            
            with col_opt1:
                if st.button("🔄 Generate New Drafts"):
                    st.rerun()
            
            with col_opt2:
                # Download drafts
                combined_drafts = f"Generated Email Replies - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                for i, draft in enumerate(drafts):
                    combined_drafts += f"=== DRAFT {i+1} ===\n{draft}\n\n"
                
                st.download_button(
                    "💾 Download All Drafts",
                    combined_drafts,
                    file_name=f"email_drafts_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
            
            with col_opt3:
                if st.button("🎯 Try Different Tone"):
                    st.info("👈 Adjust tone in the sidebar and regenerate!")
    
    else:
        st.info("📧 Please paste an email or upload a file to get started!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>✉️ AI Email Reply Assistant | Powered by Google Gemini AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()