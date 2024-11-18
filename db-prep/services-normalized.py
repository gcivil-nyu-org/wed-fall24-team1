# import boto3

# dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('services')

# response = table.scan()
# items = response['Items']

# for item in items:
#     # Check if the 'Name' attribute exists
#     if 'Name' in item:
#         normalized_name = item['Name'].lower()

#         # Update item with normalized fields
#         table.update_item(
#             Key={'Id': item['Id']},  # Use your table's primary key
#             UpdateExpression="SET NormalizedName = :n",
#             ExpressionAttributeValues={
#                 ':n': normalized_name
#             }
#         )
#     else:
#         print(f"Item {item} does not contain a 'Name' attribute.")
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("services")

response = table.scan()
items = response["Items"]

for item in items:
    # Check if the 'Name' attribute exists
    if "Name" not in item:
        # Print the item being deleted
        print(f"Deleting item: {item}")

        # Delete the item from the table
        table.delete_item(Key={"Id": item["Id"]})  # Use your table's primary key
