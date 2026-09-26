# Contributing

Great! We are happy that you are interested in contributing to the project. We welcome contributions from the community and are happy to have them.

There are many ways to contribute to this project, such as logging feature request or bugs, write code to implement new features or fix bugs, improve documentation, or simply use SecObserve and provide feedback.

A few guidelines help us to manage the project and the community and help you to contribute effectively. In addition, always have the [Code of Conduct](CODE_OF_CONDUCT.md) in mind to understand the behaviour that we expect from the community.


## Feature requests

Feature requests are logged as issues in the GitHub repository. Here are some guiding principles to help you write a well-structured feature request:

 * **Clearly describe the problem or need:** Begin by explaining the problem you are facing or the need that the feature would address. Clearly articulate why this feature would be beneficial to the project and its users.

* **Be specific:** Clearly define the feature you are requesting. Provide detailed information about what you expect the feature to do, how it should behave, and any specific requirements or functionality it should have. The more specific and well-defined your request, the easier it is for developers to understand and implement it.

* **Explain the benefits:** Describe the benefits and potential impact of implementing the feature. Explain how it would improve the project, enhance user experience, or solve a particular problem. Highlight any potential use cases or scenarios where the feature would be valuable.

* **Consider feasibility:** Take into account the project's scope, technical limitations, and the resources available to the development team. If you have any suggestions or ideas on how the feature could be implemented, provide them, but also be open to alternative approaches and the expertise of the project maintainers.


## Bug reports

A well-written bug report helps the developers understand and reproduce the problem, increasing the chances of a timely resolution. Here are a few tips to assist you in crafting a solid bug report:

* **Include a detailed description:** Provide a clear and detailed description of the bug. Include information such as what you were doing when the bug occurred, the expected behavior, and the actual behavior you observed. Be specific and provide steps to reproduce the issue if possible.

* **Provide environment details:** Mention the operating system, version, and any other relevant software or hardware configurations that might be related to the bug. This information helps the developers understand the context in which the bug is occurring.

* **Attach relevant logs or error messages:** If you encountered any error messages or have relevant log files, include them in your bug report. This can provide valuable information to the developers and assist in troubleshooting the issue.

* **Include screenshots or recordings:** If the bug is visual in nature, include screenshots or screen recordings that clearly demonstrate the problem. Visual evidence can help the developers understand the issue more effectively.

* **Isolate the problem:** If possible, try to identify the specific conditions or steps that trigger the bug. This can help the developers reproduce and debug the issue more efficiently.


## Security vulnerabilities

If you find a security vulnerability, please act responsibly and report it to us. Please do not create a public issue. Instead, use the ["Report a vulnerability"](https://github.com/SecObserve/SecObserve/security/advisories/new) button in the GitHub repository (under the "Security" tab) to report the vulnerability.


## Code contributions

Before you start working on a new feature, please have a discussion with the maintainers on the [GitHub discussions page](https://github.com/SecObserve/SecObserve/discussions). This helps to ensure that your work is aligned with the project's goals and that you are not duplicating efforts. It also gives you the opportunity to get feedback and guidance from the maintainers.


### Development process

* **Fork the repository:** Start by forking SecObserve's repository on GitHub. This creates a copy of the repository under your GitHub account.

* **Clone the repository:** Clone the forked repository to your local machine using Git. This allows you to work on the code locally.

* **Create a feature branch:** Create a new branch for your code changes, starting from the `dev` branch. Give it a descriptive name that reflects the feature or bug fix you're working on.

* **Make changes:** Use your preferred code editor to make the necessary code changes in the branch. Follow the project's coding conventions and guidelines.

* **Commit your changes:** Commit your changes using [Conventional Commits](https://www.conventionalcommits.org). This means using a specific format for your commit messages, such as <type>: <description>. The commit type can be *"feat"* for a new feature, *"fix"* for a bug fix, or *"chore"* for refactorings, documentation enhancements or other changes.

* **Push your branch:** Push your branch with the committed changes to your forked repository on GitHub.

* **Create a pull request:** Go to the SecObserve's GitHub page and create a pull request from your branch to the `dev` branch. Provide a clear and descriptive title starting with *"feat:"*, *"fix:"* or *"chore:"* and a description for your pull request.


### Code conventions

There is no strict code style guide for this project. However, have a look at the existing code and try to match the style. Several tools are used to ensure code quality which are mandatory and run on every commit:

* **Backend:** (running from the `backend` folder)

    * `black .` for code formatting
    * `isort .` for import sorting
    * `flake8` for basic linting
    * `./bin/run_mypy.sh` for type checking
    * `./bin/run_pylint.sh` for further linting

    All function signatures shall be annotated with type hints.

* **Frontend:** (running from the `frontend` folder)

    * `prettier -w src` for code formatting
    * `npm run lint` for linting

Please run these tools locally before creating a pull request to ensure that your code meets the quality standards.


### Unit tests

All new features and bug fixes in the backend shall be accompanied by unit tests. This ensures that the changes are well-tested and helps prevent regressions. The unittests are run with the commands

```bash
docker compose -f docker-compose/docker-compose-unittests.yml build
docker compose -f docker-compose/docker-compose-unittests.yml up
```

from the root directory of the project.