# Contributing to Supabase MCP Server

Thank you for your interest in Supabase MCP Server. This project aims to maintain a high quality standard I've set for it. I welcome and carefully review all contributions. Please read the following guidelines carefully.

## 🤓 Important: Pre-Contribution Requirements

1. **Required: Open a Discussion First**
   - **All contributions** must start with a GitHub Discussion before any code is written
   - Explain your proposed changes, why they're needed, and how they align with the project's vision
   - Wait for explicit approval from the maintainer before proceeding
   - PRs without a prior approved discussion will be closed immediately without review

2. **Project Vision**
   - This project follows a specific development vision maintained by the owner
   - Not all feature ideas will be accepted, even if well-implemented
   - The maintainer reserves the right to decline contributions that don't align with the project's direction

## 🛠️ Contribution Process (Only After Discussion Approval)

1. **Fork the repository:** Click the "Fork" button in the top right corner of the GitHub page.

2. **Create a new branch:** Create a branch with a descriptive name related to your contribution.
   ```bash
   git checkout -b feature/your-approved-feature
   ```

3. **Quality Requirements:**
   - **Test Coverage:** All code changes must include appropriate tests
   - **Documentation:** Update all relevant documentation
   - **Code Style:** Follow the existing code style and patterns
   - **Commit Messages:** Use clear, descriptive commit messages

4. **Make your changes:** Implement the changes that were approved in the discussion.

5. **Test thoroughly:** Ensure all tests pass and add new tests for your changes.
   ```bash
   # Run tests
   pytest
   ```

6. **Commit your changes:** Use clear, descriptive commit messages that explain what you've done.
   ```bash
   git commit -m "feat: implement approved feature X"
   ```

7. **Push your branch:** Push your changes to your forked repository.
   ```bash
   git push origin feature/your-approved-feature
   ```

8. **Create a pull request:**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select "compare across forks"
   - Select your fork and branch as the source
   - Add a detailed description that references the approved discussion
   - Include information about how you've tested the changes
   - Submit the pull request

9. **Review Process:**
   - PRs will be reviewed when time permits
   - Be prepared to make requested changes
   - The maintainer may request significant revisions
   - PRs may be rejected even after review if they don't meet quality standards

## ⚠️ Grounds for Immediate Rejection

Your PR will be closed without review if:
- No prior discussion was opened and approved
- Tests are missing or failing
- Documentation is not updated
- Code quality doesn't meet project standards
- PR description is inadequate
- Changes don't align with the approved discussion

## 🤔 Why These Requirements?

- This project is maintained by a single developer (me) with limited review time
- Quality and consistency are prioritized over quantity of contributions
- The project follows a specific vision that I want to maintain

## 🌟 Acceptable Contributions

The following types of contributions are most welcome:
- Bug fixes with clear reproduction steps
- Performance improvements with benchmarks
- Documentation improvements
- New features that have been pre-approved via discussion

## 💡 Alternative Ways to Contribute

If you have ideas but don't want to go through this process:
- Fork the project and build your own version
- Share your use case in Discussions
- Report bugs with detailed reproduction steps

Thank you for understanding and respecting these guidelines. They help maintain the quality and direction of the project.
