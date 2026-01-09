Quality Assurance & Testing
===========================

In ManagerX, we focus on manual verification and functional integrity rather than using external testing libraries.

How to Verify Your Changes
--------------------------

Before submitting a Pull Request, please ensure the following:

1. **Manual Functional Test**: 
   Run the application and manually trigger the feature you changed. Verify that it behaves exactly as described in your PR.

2. **No Regression**: 
   Check that your changes do not break existing core functionalities of ManagerX.

3. **Log Check**:
   Monitor the console output or log files while running your changes to ensure no new warnings or errors are being triggered.

4. **Environment Check**:
   Ensure your code runs in the standard development environment without requiring additional, unlisted dependencies.

.. warning::
   Code that causes the application to crash or introduces obvious logic errors will be sent back for revision.