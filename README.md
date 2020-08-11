# Pulumi Amplify Proof-of-concept

This repository is a proof-of-concept of a GraphQL application using AppSync and Cognito which is managed entiely by Pulumi.  This project also makes use of AWS Amplify as a code generator, but not as a cloud provisioner.

This example implements a React app which allows users to create simple notes which are stored in a database.  The notes can only be updated and deleted by their original creator.

**To deploy this example**:

* Checkout the repo and create and enter a Python venv
* Run `pip install -r requirements.txt`
* Run `amplify init` and confirm that you will use the existing environment `dev`
* Run `amplify api gql-compile` to generate code in the `amplify` directory
* Run `pulumi up` to create the cloud resources based on `amplify`
* Run `npm install` to install the frontend dependencies
* Run `npm start` and view the given localhost URL in your browser


**To update the schema:**

If the schema is changed, you must use Amplify to regenerate the necessary code:

* `amplify codegen` to rebuild the client helper classes
* `amplify api gql-compile` to rebuild the backend schema and resolvers
* `pulumi up` to push the new backend configuration to AppSync


**To use this Pulumi code with a new Amplify project:**

If you wish to create a new application based on this example, you should start with an empty directory and start to create an Amplify project:

* `amplify init`
* `amplify add api`
  * You MUST choose Cognito for authentication.  Any settings you provide for Cognito are ignored, as the Pulumi script will create its own.
* `amplify codegen add`
* _Do **not** call `amplify push`!_
* Copy `__main__.py` from this project
* Modify the `graphql_types` and `amplify_api_name` name variables to match your Amplify project



## Known issues and limitations:

* Although Amplify does not push any of the cloud resources for the API or Cognito, it will still create an Amplify app and deployment bucket which serve no purpose
* The Pulumi program assumes a DynamoDB backend
* The Dynamo tables have only a single hash key called `id` each
* The Pulumi program assumes Cognito for authentication

# React frontend

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).


## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.<br />
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.<br />
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.<br />
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.<br />
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.<br />
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: https://facebook.github.io/create-react-app/docs/code-splitting

### Analyzing the Bundle Size

This section has moved here: https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size

### Making a Progressive Web App

This section has moved here: https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app

### Advanced Configuration

This section has moved here: https://facebook.github.io/create-react-app/docs/advanced-configuration

### Deployment

This section has moved here: https://facebook.github.io/create-react-app/docs/deployment

### `npm run build` fails to minify

This section has moved here: https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify
