# SweetfxDB

## Project Overview

SweetFX, ReShade, and similar tools are universal image improvement and tweaking mods for PC games. They allow users to apply a suite of post-processing shader effects to their games, such as sharpening, color correction, and anti-aliasing, to enhance the visual experience.

sfx.thelazy.net is a web application that serves as a comprehensive database for presets for SweetFX, ReShade, and similar graphics modification tools. This platform enables users to easily browse, download, and share customized settings for a wide variety of games. Key features include:

*   **Preset Database:** A vast collection of user-submitted presets for tools like SweetFX and ReShade, categorized by game.
*   **Game List:** An extensive list of games compatible with these modification tools, making it easy to find presets for specific titles.
*   **Forum:** A community forum for users to discuss presets, share tips, and seek help related to these graphics modification tools.
*   **Downloads:** A system for managing preset downloads and tracking popular settings.

Code for sfx.thelazy.net

## To set up:

### Prerequisites

*   **Docker:** Ensure Docker is installed on your system.
*   **Docker Compose:** Ensure Docker Compose is installed on your system.
*   **Note:** The Docker image uses Python 3.10.

### Steps

1.  **Build and run the application:**
    ```bash
    docker-compose up --build
    ```
2.  **Access the application:**
    Open your web browser and navigate to `http://localhost:8124/` (or `http://127.0.0.1:8124/`).
3.  **Create an admin user (optional):**
    If you need an admin user, run the following command in a separate terminal:
    ```bash
    docker-compose exec sweetfx python manage.py createsuperuser
    ```
    Follow the prompts to create the superuser.
4.  **Reset stored data and database (use with caution):**
    To remove all data, including the SQLite database and any uploaded media, run:
    ```bash
    docker-compose down -v
    ```
    **Warning:** This command is destructive and will permanently delete your data.

## Contributing

We welcome contributions to improve sfx.thelazy.net! Here's how you can help:

### Reporting Issues

If you encounter a bug or have a suggestion for a new feature:

1.  **Check existing issues:** Before submitting, please browse the "Issues" tab on the GitHub repository page to see if someone else has already reported it or suggested the same feature.
2.  **Open a new issue:** If your issue or suggestion is new, please open a new issue using the "Issues" tab on the GitHub repository page.
3.  **Provide details:**
    *   For bugs, include steps to reproduce, what you expected to happen, and what actually happened. Screenshots can be very helpful.
    *   For feature requests, clearly describe the proposed feature and why it would be beneficial.

### Pull Requests

If you'd like to contribute code:

1.  **Fork the repository:** Create your own fork of the main repository.
2.  **Create a new branch:** Switch to a new branch for your changes. Use a descriptive name, for example:
    *   `git checkout -b feature/your-awesome-feature`
    *   `git checkout -b fix/bug-description-or-issue-number`
3.  **Make your changes:** Implement your feature or bug fix.
4.  **Commit your changes:** Write clear and concise commit messages.
5.  **Push to your fork:** Push your branch to your forked repository.
    ```bash
    git push origin feature/your-awesome-feature
    ```
6.  **Open a Pull Request:** Go to the main repository and open a pull request from your branch to the `main` (or `master`) branch.
    *   Provide a clear description of your changes in the pull request.
    *   Reference any related issues.

**General Guidelines:**

*   **Tests:** If you're adding new functionality or fixing a bug, please try to include tests if applicable.
*   **Code Style:** Try to follow the existing code style of the project. (While a formal style guide is not yet established, consistency is appreciated.)

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for the full license text.
