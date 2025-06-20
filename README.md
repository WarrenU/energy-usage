# Energy Usage Upload API

This project provides a FastAPI backend for uploading energy usage data from CSV files. 
Data is stored in a local DynamoDB instance.
Data uploaded is written to a mock_s3 directory. (local s3 setup)
A simple HTML frontend allows you to upload many csv files (or others) at once.


## Requirements
- Python 3.8+
- pip
- Java 17+ (for DynamoDB Local)
- Docker (optional, for running DynamoDB Local via container)
- AWS CLI (for table setup, install globally)

## Setup

### 1. (Recommended) Create and Activate a Python Virtual Environment
It is best practice to use a virtual environment to manage dependencies for this project.

#### On Windows:
```
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```
python3 -m venv venv
source venv/bin/activate
```

To deactivate the virtual environment when done, simply run:
```
deactivate
```

### 2. Install Python dependencies
Install all required Python packages using:
```
pip install -r requirements.txt
```

### 3. (One-time) Install the AWS CLI Globally
The AWS CLI is required only for creating the DynamoDB table, not for running the backend. Install it globally (not in your venv):

- [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Or with pip:
  ```
  pip install --user awscli
  ```

### 4. Start DynamoDB Local
You must have a local DynamoDB instance running on port 8000.

#### Using Docker
```
docker run -p 8000:8000 amazon/dynamodb-local
```

### 5. Create the DynamoDB Table
Once DynamoDB Local is running, you need to create the required table. This is done using the AWS CLI.

#### Step 2: Configure the AWS CLI for Local Use
You can use any values for AWS credentials, as DynamoDB Local does not require real credentials. Run:
```
aws configure
```
When prompted, you can use these example values:
- AWS Access Key ID: `fakeMyKeyId`
- AWS Secret Access Key: `fakeSecretAccessKey`
- Default region name: `us-west-2`
- Default output format: `json`

#### Step 3: Create the Table
With DynamoDB Local running (in another terminal), run the following command in your terminal (as a single line):
```
aws dynamodb create-table --table-name EnergyUsage --attribute-definitions AttributeName=userId,AttributeType=S AttributeName=date,AttributeType=S --key-schema AttributeName=userId,KeyType=HASH AttributeName=date,KeyType=RANGE --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 --endpoint-url http://localhost:8000
```
If successful, you will see a JSON response describing the new table.

## Viewing Data in DynamoDB Local

To see the data you have saved in your local DynamoDB, you can use the AWS CLI to scan the table and print all items:

```
aws dynamodb scan --table-name EnergyUsage --endpoint-url http://localhost:8000
```

This will output all records in the `EnergyUsage` table as JSON.


## Running the Backend
```
uvicorn backend.main:app --reload
```

The API will be available at http://127.0.0.1:8000



## Serving the Frontend Locally
You can use Python's built-in HTTP server to serve the frontend:

From the project root (where `frontend.html` is located), run:

```
python -m http.server 8080
```

Then open [http://localhost:8080/frontend.html](http://localhost:8080/frontend.html) in your browser.

## Editing the Threshold in the UI
When using the frontend, you can set the usage threshold for alerts by editing the "Threshold" input field above the upload button. Enter any number (including negative values) to set your desired threshold before uploading your files.

## Notes on API Gateway
In this project, FastAPI serves as the API layer, standing in for Amazon API Gateway in a local/mock environment. In a production AWS deployment, API Gateway would be used as the entry point to the backend.

## Deploying to AWS: ECS Behind API Gateway
To deploy this project in a production AWS environment, you could:
1. **Containerize the FastAPI app** using Docker.
2. **Push the Docker image** to Amazon ECR (Elastic Container Registry).
3. **Deploy the container** to Amazon ECS (Elastic Container Service), using either Fargate or EC2 launch types.
4. **Provision DynamoDB** (managed, not local) and S3 (for real file storage) in AWS.
5. **Set up an Amazon API Gateway** to route HTTP(S) requests to your ECS service using a VPC Link.
6. **Configure environment variables** and IAM roles for secure access to DynamoDB and S3.

---

## Trade-offs

- **Single File Backend:** All backend logic is in `main.py` for simplicity and ease of review. For larger or production projects, splitting into multiple modules (routes, services, models) would improve maintainability and scalability.
- **FastAPI as API Gateway Stand-in:** FastAPI is used locally to mock API Gateway. In production, API Gateway would provide additional features like request validation, throttling, and security.
- **Mock S3 and Local DynamoDB:** Files are saved to a local directory (mock S3) and DynamoDB Local is used for development. In production, you would use AWS S3 and managed DynamoDB for durability, scalability, and security.
- **No Authentication:** The project does not implement authentication or authorization for simplicity. In a real-world scenario, you would secure the API endpoints.
- **Minimal Frontend:** The frontend is a simple HTML/JS/CSS app for demonstration. For a richer user experience, a framework like React could be used.
- **No Automated Testing:** There are no automated tests included. For production, unit and integration tests are recommended.

These trade-offs were made to keep the project focused, easy to run locally.

---