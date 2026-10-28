# Connecting Instagram and Facebook (one time, about 20–30 minutes)

Meta changes these screens often, so button names may differ slightly. If something doesn't match,
take a screenshot and ask. **Never share the App Secret or access token**: they work like passwords.

## 1. Make your Instagram a Professional account

In the Instagram app: **Profile → ☰ menu → Settings → Account type and tools → Switch to professional
account**. Choose **Creator** (or Business). It's free and you can switch back.

## 2. Have a Facebook Page and link Instagram to it

- No Page yet? On Facebook: **Menu → Pages → Create new Page**.
- Link them: open the Page → **Settings → Linked accounts → Instagram → Connect**, and log in to Instagram.
  (Alternatively in the Instagram app: **Settings → Accounts Center** and add the Facebook account and Page.)

## 3. Create a Meta developer app

1. Go to https://developers.facebook.com, log in with your Facebook account, and click **Get Started**
   if it's your first time (it asks you to verify your account).
2. **My Apps → Create App**. Give it any name (e.g. "UGC Poster").
3. When asked what the app is for, choose the option for managing **Pages / Instagram content**
   (or **Other → Business** if offered).
4. Once created, open **App settings → Basic**. You'll need the **App ID** and **App Secret**
   (click "Show") in step 5.

The app can stay in **Development** mode: you're its admin, and it only posts to your own accounts.

## 4. Generate a token in Graph API Explorer

1. Go to https://developers.facebook.com/tools/explorer
2. On the right, pick your app under **Meta App**.
3. Under **User or Page**, choose **Get User Access Token**.
4. Add these permissions:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`,
   `instagram_content_publish`, `business_management`
5. Click **Generate Access Token**. In the pop-up, tick your **Page** and your **Instagram account**,
   and allow everything.
6. Copy the long code that appears in the **Access Token** box.

## 5. Run setup

Double-click **setup.bat** in the project folder and paste the App ID, App Secret and access token when
asked (right-click pastes in the black window). If you have more than one Facebook Page, pick the one
your Instagram is linked to.

It turns the token into a long-lasting key and saves it in `settings.json` on your PC. You only need to
do this again if the key stops working (for example after changing your Facebook password).
