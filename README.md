# STILL UNDER DEVELOPMENT!!!

# Final project
- Course: Deep Azure
- Project: Conversion of X12 documents to XML format, using Azure Batch
- Student: Martin Bertrand

# Problem statement:

The company I work at receives EDI transactions from many business partners (clients and manufacturers).  These files are received and transformed by Tibco products, running on local servers.  

The infrastructure is sufficient to process the regular flow of transactions, with the exception of infrequent, but regular, large batches from certain clients.  These batches can contain up to 40 000 distinct files, sent as fast as the network will permit.  A performance bottleneck has been identified in the transform step.  The original X12 files must be transformed into XML files, and sent to the backend server.

# Proposed solution

This project will demonstrate how Azure Batch service could be used to provide my company an automatically scalable EDI transformation solution.  It will transform X12 documents into XML files, using auto-scale and task queuing functionalities of Azure Batch.

# Azure Batch

Azure Batch is particularly well suited for this type of problem.  It provides a platform for running parallel, high-performance computing.  In the context of this project, it will allow the solution to automatically scale and parallel process the large number of EDI files received.  The transformation bottleneck of the whole EDI solution will therefore be greatly reduced.

# Results

This project provides code to create the Azure Batch infrastructure and run a sample X12 to XML batch transformation.  

# Limitations

This project is a technology demonstration, not a real production solution.  Processing a real batch would incur costs that cannot be justified in the context of this Azure course.  The parameters used are therefore not optimal to minimize the total processing time.  Further load testing and tuning is required to meet production targets.

# Links:

- 2 minutes YouTube presentation: WORKING ON IT!
- 15 minutes YouTube presentation: WORKING ON IT!

# If you want to use the code...

Read the file Azure-Batch_Martin-Bertrand_Report.pdf, it demonstrates how to use the code, with expected results in Azure and troubleshooting tips.
