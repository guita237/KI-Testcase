import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def create_html_template(name, content, link, app_name, email_type="verify"):
    """
    Creates a beautiful HTML email template - Blue Theme
    """

    # Blue palette for your app
    primary_blue = "#3b82f6"      # Main blue
    secondary_blue = "#2563eb"    # Darker blue (hover)
    light_blue = "#dbeafe"        # Very light blue (background)
    gradient_start = "#3b82f6"    # Gradient start
    gradient_end = "#1d4ed8"      # Gradient end

    # Colors and text according to email type
    if email_type == "verify":
        button_color = primary_blue
        title = "Email Verification"
        icon = "✉️"
    elif email_type == "reset":
        button_color = secondary_blue
        title = "Password Reset"
        icon = "🔐"
    else:  # modification
        button_color = "#4f46e5"  # Indigo
        title = "Email Changed"
        icon = "📧"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @media only screen and (max-width: 600px) {{
                .container {{ width: 100% !important; }}
                .button {{ width: 90% !important; text-align: center !important; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f0f9ff;">
        
        <!-- Main container -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #f0f9ff 0%, #e6f0fa 100%); padding: 40px 20px;">
            <tr>
                <td align="center">
                    <!-- Email card -->
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 24px; box-shadow: 0 20px 35px -8px rgba(59, 130, 246, 0.15), 0 10px 10px -5px rgba(0, 0, 0, 0.02); overflow: hidden; border: 1px solid rgba(59, 130, 246, 0.1);" class="container">
                        
                        <!-- Header with blue gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, {gradient_start} 0%, {gradient_end} 100%); padding: 40px 30px; text-align: center;">
                                <div style="font-size: 52px; color: white; margin-bottom: 15px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));">{icon}</div>
                                <h1 style="color: white; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">{app_name}</h1>
                                <div style="width: 60px; height: 3px; background-color: rgba(255,255,255,0.3); margin: 15px auto 0 auto; border-radius: 50px;"></div>
                                <p style="color: rgba(255,255,255,0.95); margin: 15px 0 0 0; font-size: 16px; font-weight: 400;">{title}</p>
                            </td>
                        </tr>
                        
                        <!-- Main content -->
                        <tr>
                            <td style="padding: 45px 35px;">
                                <h2 style="color: #1e293b; margin: 0 0 15px 0; font-size: 24px; font-weight: 600;">Hello {name}!</h2>
                                
                                <div style="width: 50px; height: 3px; background: linear-gradient(90deg, {primary_blue}, {light_blue}); margin: 0 0 25px 0; border-radius: 50px;"></div>
                                
                                <p style="color: #334155; line-height: 1.7; margin: 0 0 25px 0; font-size: 16px;">
                                    {content}
                                </p>
                                
                                <!-- Styled action button -->
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 15px 0 25px 0;">
                                            <a href="{link}" class="button" style="display: inline-block; background: linear-gradient(135deg, {primary_blue}, {secondary_blue}); color: white; text-decoration: none; padding: 16px 45px; border-radius: 50px; font-weight: 600; font-size: 16px; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3); transition: all 0.2s ease; border: none;">{get_button_text(email_type)}</a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Additional info with light blue background -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: {light_blue}; border-radius: 16px; margin: 20px 0 0 0; border: 1px solid rgba(59, 130, 246, 0.2);">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="color: #1e40af; margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">🔗 Direct link:</p>
                                            <p style="color: {primary_blue}; font-size: 13px; margin: 0; word-break: break-all; line-height: 1.5;">
                                                <a href="{link}" style="color: {primary_blue}; text-decoration: underline;">{link}</a>
                                            </p>
                                            <p style="color: #2563eb; margin: 15px 0 0 0; font-size: 13px; font-style: italic;">
                                                ⏱️ This link expires in 1 hour
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Very light blue footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 2px solid {light_blue};">
                                <p style="color: #475569; margin: 0 0 15px 0; font-size: 14px;">
                                    <span style="display: inline-block; background-color: {light_blue}; padding: 5px 12px; border-radius: 50px; color: {secondary_blue}; font-size: 12px; font-weight: 500;">🔒 Secured by {app_name}</span>
                                </p>
                                <p style="color: #64748b; margin: 0 0 5px 0; font-size: 13px;">
                                    If you didn't request this email, you can safely ignore it.
                                </p>
                                <p style="color: #94a3b8; margin: 15px 0 0 0; font-size: 12px;">
                                    © 2025 {app_name}. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Help text -->
                    <p style="color: #64748b; margin-top: 25px; font-size: 13px;">
                        Need help? <a href="mailto:{app_name.lower()}@web.de" style="color: {primary_blue}; text-decoration: none; font-weight: 500;"></a>
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

def get_button_text(email_type):
    """Returns button text based on email type"""
    texts = {
        "verify": " Verify my email address",
        "reset": " Reset my password",
        "modify": " Confirm change"
    }
    return texts.get(email_type, "Confirm")

def send_verification_email(name, email, verification_link):
    """Verification email - Blue theme"""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    app_name = os.getenv('APP_NAME', 'Application')

    content = f"""
    Thank you for signing up for <span style="color: #3b82f6; font-weight: 600;">{app_name}</span>! 
    
    To complete your registration and enjoy all features, we need to verify your email address.
    
    <span style="display: block; margin-top: 15px;">✨ This will only take a minute!</span>
    """

    # Plain text version
    text = f"""
    Hello {name},

    Thank you for signing up for {app_name}!

    To complete your registration, please verify your email address by clicking the link below:
    {verification_link}

    This link will expire in 1 hour.

    If you didn't create an account with {app_name}, you can safely ignore this email.

    Best regards,
    The {app_name} Team
    """

    # Create multipart message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f' Verify your email - {app_name}'
    msg['From'] = f"{app_name} <{smtp_email}>"
    msg['To'] = email

    # HTML version
    html = create_html_template(name, content, verification_link, app_name, "verify")

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        print(f" Verification email sent to {email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise

def send_reset_password(name, email, reset_link):
    """Password reset email - Blue theme"""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    app_name = os.getenv('APP_NAME', 'Application')

    content = f"""
    We received a request to reset the password for your <span style="color: #3b82f6; font-weight: 600;">{app_name}</span> account.
    
    If you made this request, click the button below to set a new secure password.
    
    <span style="display: block; margin-top: 15px; color: #64748b; font-size: 14px;">⏰ For security reasons, this link will expire in 1 hour.</span>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f' Reset your password - {app_name}'
    msg['From'] = f"{app_name} <{smtp_email}>"
    msg['To'] = email

    text = f"""
    Hello {name},

    We received a request to reset the password for your {app_name} account.

    To reset your password, click this link:
    {reset_link}

    This link will expire in 1 hour.

    If you didn't request a password reset, you can safely ignore this email.

    Best regards,
    The {app_name} Team
    """

    html = create_html_template(name, content, reset_link, app_name, "reset")

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        print(f" Password reset email sent to {email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise

def send_modification_email(name, email, verification_link):
    """Email change confirmation - Blue theme"""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    app_name = os.getenv('APP_NAME', 'Application')

    content = f"""
    Your sign-in email address for <span style="color: #3b82f6; font-weight: 600;">{app_name}</span> has been changed.
    
    <div style="background-color: #dbeafe; padding: 15px; border-radius: 12px; margin: 15px 0;">
        <span style="color: #1e293b;">New address:</span>
        <span style="color: #3b82f6; font-weight: 600; word-break: break-all;">{email}</span>
    </div>
    
    To confirm this change and secure your account, please verify your new email address.
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f' Confirm your new email - {app_name}'
    msg['From'] = f"{app_name} <{smtp_email}>"
    msg['To'] = email

    text = f"""
    Hello {name},

    Your sign-in email address for {app_name} has been changed to: {email}

    To confirm this change, click this link:
    {verification_link}

    If you didn't make this change, please contact us immediately.

    Best regards,
    The {app_name} Team
    """

    html = create_html_template(name, content, verification_link, app_name, "modify")

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        print(f" Email change confirmation sent to {email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise