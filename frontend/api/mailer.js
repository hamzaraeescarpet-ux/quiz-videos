import nodemailer from 'nodemailer';

export default async function handler(req, res) {
  // We only accept POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { to, subject, text } = req.body;

  if (!to || !subject || !text) {
    return res.status(400).json({ error: 'Missing required fields: to, subject, text' });
  }

  // Get credentials from Vercel Environment Variables
  const senderEmail = process.env.GMAIL_SENDER_EMAIL;
  const appPassword = process.env.GMAIL_APP_PASSWORD;

  if (!senderEmail || !appPassword) {
    console.error("Missing Vercel Environment Variables: GMAIL_SENDER_EMAIL or GMAIL_APP_PASSWORD");
    return res.status(500).json({ error: 'Server is missing email configuration.' });
  }

  try {
    // Create a Nodemailer transporter using Gmail
    let transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: senderEmail,
        pass: appPassword
      }
    });

    // Send the email
    let info = await transporter.sendMail({
      from: `"QuizViral AI" <${senderEmail}>`,
      to: to,
      subject: subject,
      text: text,
    });

    console.log("Message sent: %s", info.messageId);
    return res.status(200).json({ success: true, messageId: info.messageId });
  } catch (error) {
    console.error("Error sending email:", error);
    return res.status(500).json({ error: 'Failed to send email', details: error.toString() });
  }
}
