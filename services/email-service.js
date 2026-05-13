/**
 * Email service for authentication
 */

/**
 * Send verification email to user
 * @param {string} email - User's email address
 * @param {string} token - Verification token
 */
const sendVerificationEmail = (email, token) => {
  const verifyUrl = `http://localhost:3000/api/auth/verify?token=${token}`;

  const htmlTemplate = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Verify Your Email</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h2 style="color: #4CAF50;">Verify Your Email Address</h2>
    <p>Hello,</p>
    <p>Thank you for registering! Please click the button below to verify your email address:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="${verifyUrl}" style="display: inline-block; background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Verify Email</a>
    </div>
    <p>Or copy and paste this link into your browser:</p>
    <p style="background-color: #f1f1f1; padding: 10px; border-radius: 4px; word-break: break-all;">${verifyUrl}</p>
    <p style="margin-top: 30px; font-size: 12px; color: #666;">This link will expire in 30 minutes.</p>
    <p>If you did not create an account, please ignore this email.</p>
  </div>
</body>
</html>`;

  console.log(`[Email Service] Verification email sent to ${email}`);
  console.log(`[Email Service] URL: ${verifyUrl}`);

  // In production, use Nodemailer here
  // return nodemailer.sendMail({ ... });
};

/**
 * Send password reset email to user
 * @param {string} email - User's email address
 * @param {string} token - Password reset token
 */
const sendResetEmail = (email, token) => {
  const resetUrl = `http://localhost:3000/api/auth/reset/confirm?token=${token}`;

  const htmlTemplate = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Password Reset</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
    <h2 style="color: #FF9800;">Password Reset Request</h2>
    <p>Hello,</p>
    <p>You have requested to reset your password. Click the button below to proceed:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="${resetUrl}" style="display: inline-block; background-color: #FF9800; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
    </div>
    <p>Or copy and paste this link into your browser:</p>
    <p style="background-color: #f1f1f1; padding: 10px; border-radius: 4px; word-break: break-all;">${resetUrl}</p>
    <p style="margin-top: 30px; font-size: 12px; color: #666;">This link will expire in 30 minutes.</p>
    <p>If you did not request a password reset, please ignore this email. Your password will remain unchanged.</p>
  </div>
</body>
</html>`;

  console.log(`[Email Service] Password reset email sent to ${email}`);
  console.log(`[Email Service] URL: ${resetUrl}`);

  // In production, use Nodemailer here
  // return nodemailer.sendMail({ ... });
};

module.exports = {
  sendVerificationEmail,
  sendResetEmail
};
