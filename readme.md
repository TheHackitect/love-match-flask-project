# Love & Dating Website Project

## Introduction
This project is a Love & Dating website developed using Python Flask, Bootstrap, and jQuery. The website provides a captivating platform for users to find their perfect match, make friends, and connect with amazing people. The project includes user-facing pages such as the home page, sign-up page, sign-in page, and user dashboard, as well as an admin dashboard for site management.

## Features
1. **Home Page**:
    - Captivating design with a purple and pink color scheme.
    - Jumbotron with a welcome message.
    - Six bootstrap cards explaining the site’s purpose.
    - Sign-in and sign-up buttons.

2. **Sign-Up Page**:
    - Collects user information: Name, Phone number, Email, Telegram User ID, Password, Confirm Password, Dating Preference, Short Bio, How did you hear about us, and Event notifications.
    - Real-time data verification using jQuery.
    - Links to sign in and forgot password.

3. **Sign-In Page**:
    - Simple form to collect email and password.
    - Links to sign up and forgot password.

4. **User Dashboard**:
    - Displays user information: Name, Date joined, Phone Number, Email, Telegram ID, Bio, Unique number, My matches.
    - Matches are displayed as clickable Bootstrap cards.
    - Action buttons: Edit, Find Match, Telegram Bot, Telegram Channel.

5. **Admin Dashboard**:
    - Navigation sidebar for easy access to different sections.
    - Overview section with key metrics.
    - User management table with edit and delete options.
    - Sections for site analytics, reports, and settings.

## Technologies Used
- **Frontend**:
    - HTML, CSS, Bootstrap
    - FontAwesome for icons
    - jQuery for real-time data verification

- **Backend**:
    - Python Flask

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo/love-and-dating-website.git
    cd love-and-dating-website
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the Flask application:
    ```bash
    flask run
    ```

5. Open your browser and navigate to `http://127.0.0.1:5000` to see the website.

## File Structure
```bash
love-and-dating-website/
│
├── static/
│ ├── css/
│ │ └── styles.css
│ └── js/
│ └── scripts.js
│
├── templates/
│ ├── base.html
│ ├── home.html
│ ├── sign_up.html
│ ├── sign_in.html
│ ├── user_dashboard.html
│ └── admin_dashboard.html
│
├── app.py
├── requirements.txt
└── README.txt
```


## Usage
- **Home Page**: Accessible at `/`.
- **Sign-Up Page**: Accessible at `/sign_up`.
- **Sign-In Page**: Accessible at `/sign_in`.
- **User Dashboard**: Accessible at `/dashboard`.
- **Admin Dashboard**: Accessible at `/admin`.

## Contributions
Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.

## Acknowledgements
- Bootstrap: [https://getbootstrap.com/](https://getbootstrap.com/)
- FontAwesome: [https://fontawesome.com/](https://fontawesome.com/)
- jQuery: [https://jquery.com/](https://jquery.com/)

