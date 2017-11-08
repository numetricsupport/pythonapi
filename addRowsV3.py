def addRows(df, tableid, chunkSize=1000):
    '''
    Adds all rows from a pandas dataframe, in batches of chunkSize, to the specified Numetric table

    Uses pandas and requests packages

    :param df: pandas dataframe containing data
    :param tableid: Numetric tableid of the target warehouse table
    :param apiKey: Numetric apiKey for your organization
    :param chunkSize: number of rows to send in each sequential API call. Default is 1000 rows.

    '''

    # logger and apiKey come from elsewhere.
    global logger, apiKey

    # Calculate number of iterations required to get through the dataset, given its length, and extract number of rows, too
    iterations = math.ceil(len(df) / chunkSize)
    nrows = len(df)

    # now iterate through [iterations] number of times, sending chunks of data each time
    for i in range(1, iterations + 1):  # +1 in range because of Python's iteration paradigm (excludes last item in range)
        # get starting and ending index numbers
        startNum = ((i - 1) * chunkSize)
        endNum = i * chunkSize

        # But also truncate when we go past nrows (happens on last chunk)
        if endNum > nrows + 1:
            endNum = nrows + 1

        # Subset dataframe and convert to appropriate JSON object
        thisChunk = df[startNum:endNum]
        dataToSend = thisChunk.to_json(orient='records')

        # Final assembly of the payload for the API call
        payload = "{\"rows\":" + dataToSend + "}"

        # Now initiate the API call

        # URL for adding rows to this table
        url = "https://api.numetric.com/v3/table/" + tableid + "/rows"

        # Incorporate the API Key for authorization
        headers = {'authorization': apiKey,
                   'Content-Type': "application/json"}

        # Make the API call, capturing the response code
        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            # print(response.text)
            # print(response.content)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(e)
            logger.error("HTTP Gateway Error encountered. Retrying a few times...")
            time.sleep(30)
            for i in range(3):
                try:
                    response = requests.request("POST", url, data=payload, headers=headers)

                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    logger.error(e)
                    logger.error("API still not responding. Trying again.")
                    time.sleep(30)
        except requests.exceptions.RequestException as e:
            logger.error("HTTP Gateway Error encountered.")
            logger.error(e)

        # If we're on the last iteration, report that it was successful.
        if (iterations == 1) or (i == iterations):
            logger.info("100% processed, sending command to process new data.")
        # Otherwise, report progress.
        else:
            logger.info("%s percent processed, starting with row %s", str(round(endNum / nrows * 100)), str(endNum))
    sendIndexCommand(tableid)
