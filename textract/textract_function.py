import boto3
import time

def start_job(s3BucketName, objectName):
    response = None
    client = boto3.client('textract')
    response = client.start_document_text_detection(
    DocumentLocation={
        'S3Object': {
            'Bucket': s3BucketName,
            'Name': objectName
        }
    })

    return response["JobId"]


def is_job_complete(jobId):
    """
    That function is responsible to validate if a started job in textract is completed or not
    """
    time.sleep(5)
    client = boto3.client('textract')
    response = client.get_document_text_detection(JobId=jobId)
    status = response["JobStatus"]
    print("Job status: {}".format(status))

    try:
        while(status == "IN_PROGRESS"):
            time.sleep(5)
            response = client.get_document_text_detection(JobId=jobId)
            status = response["JobStatus"]
            print("Job status: {}".format(status))

        return True
    except Exception as e:
        print(str(e))
        return False


def get_job_results(jobId):
    pages = []

    time.sleep(5)

    client = boto3.client('textract')
    response = client.get_document_text_detection(JobId=jobId)
    
    pages.append(response)
    print("Resultset page recieved: {}".format(len(pages)))
    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']

    # Next token necessary because the number of pages is huge
    while(nextToken):
        response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)

        pages.append(response)
        print("Resultset page recieved: {}".format(len(pages)))
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']

    return pages


def write_extract_to_file(response, documentNametxt):
    # write detected text into a txt file
    for result_page in response:
        for item in result_page["Blocks"]:
            if item["BlockType"] == "LINE":
                with open(documentNametxt, "a+") as file_object:
                    # Move read cursor to the start of file.
                    file_object.seek(0)
                    # If file is not empty then append '\n'
                    data = file_object.read(100)
                    if len(data) > 0 :
                        file_object.write("\n")
                    # Append text at the end of file
                    file_object.write(item["Text"])


if __name__ == "__main__":

    # S3 file will be passed as an event to the Lambda function.
    s3BucketName = "textract-test-aneel"
    documentName = "textract/input/o_cortico.pdf"

    job_id = start_job(s3BucketName, documentName)
    print("Started job with id: {}".format(job_id))

    # Loop over function
    validation = is_job_complete(job_id)

    if not validation:
        print("Error when validate the JOB")
        
    response = get_job_results(job_id)

    # Change the format of document to TXT
    documentNametxt = ((documentName.split("/")[-1]).split(".")[0])+".txt"
    
    write_extract_to_file(response, documentNametxt)

    # Upload file to S3


    