When dealing with issues relating to a CLI application like Claude Code and its connection to WebSocket servers, there are several potential causes and behaviors to consider. Here are some things to look into based on your description:

1. **Configuration Loading**: Ensure that the `mcp.json` configuration is being loaded correctly. If there are any issues with the file path or content, it may fall back to stdio-based servers without logging an error.

2. **Transport Type Validity**: Check that the transport type specified (`"ws"`) is supported by the version of Claude Code you are using. If there's a mismatch between the expected transport types and what is configured, it could lead to silent failures.

3. **Graceful Fallback**: The application may be designed to fail gracefully. If it detects that it cannot establish a WebSocket connection, it might fall back to stdio-based servers without logging details. Look for any configuration or command arguments that might control logging verbosity, which could provide insights on what's happening under the hood.

4. **Logging Configuration**: Examine if there's a setting that adjusts the logging level or enables more verbose output. By increasing the logging verbosity, you may be able to get more information about what operations the application is performing and why it's not attempting a WebSocket connection.

5. **Error Handling**: If the configuration file is malformed or there's some other issue (like network issues with the WebSocket server), the CLI tool might contain error handling that skips over the connection attempt entirely.

6. **Documentation and Issues**: Review the official documentation for the version you're using to verify if there are any known issues or special requirements when using WebSocket transport. Additionally, check for any open issues in the project’s repository that pertain to WebSocket connectivity. 

7. **Debugging**: If possible, run the application with debugging options or under a debugger to inspect the initialization phase. This may give you insights into whether the configuration is being processed as expected.

8. **Network Tools**: Use network tools (like `telnet`, `curl`, or WebSocket client libraries) to manually test the connectivity to `ws://localhost:8000?upstream=fiedler` to ensure that the WebSocket server is indeed accessible from your machine and responsive.

If after checking the above aspects the issue is still unclear, you might want to reach out to the support channels specific to Claude Code, such as forums, GitHub issues, or any community group they have set up, where someone could provide more tailored assistance based on the specifics of the application.