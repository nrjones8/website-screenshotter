import boto3

if __name__ == "__main__":

    bucket = 'news-screenshots-bucket'
    photo = 'raw-screenshots/nytimes.com/2019/4/23/11/2/screenshot.png'

    client = boto3.client('rekognition', region_name='us-west-2')
  
    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':photo}})
                        
    textDetections=response['TextDetections']
    print ('Detected text')
    for text in textDetections:
            print ('Detected text:' + text['DetectedText'])
            print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            print ('Id: {}'.format(text['Id']))
            if 'ParentId' in text:
                print ('Parent Id: {}'.format(text['ParentId']))
            print ('Type:' + text['Type'])
            print
