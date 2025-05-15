# Quick start

Fork the repository, and start a new codespace via the github UI.

Read the [manual](https://xzetsubou.github.io/hass-localtuya/).

## Manual setup

As above.

Python 3.12 or higher.

`pip install -r requirements_test.txt`

Validate your installation with:

`pytest`

Optionally, install the pre-commit hook(s):

```cp contrib/pre-commit .git/hooks/ && chmod +x .git/hooks/pre-commit```

## Contributing

- Run `black` and `codespell` to ensure your code passes CI.
- Bonus points for adding test coverage.
- If you utilise an AI agent, please disclose in your pull request. (They can be very useful, but also get things very wrong some times)
