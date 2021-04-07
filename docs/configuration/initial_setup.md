# `adjuftments` Configuration

## Airtable Configuration

### Create Your Base

1) Open
   this [Template Base](https://airtable.com/invite/l?inviteId=inv0k83ie8uoQg1u6&inviteToken=13d0c39a14edd83fc6e9c8951e0b8176aa38c0982257a58b294873afcedbfbe8)
   and create a duplicate.

2) Populate the `budgets` and `miscellaneous` tables inside of `Splitwise`.
    - Budgets Table:
        - `Proposed Budget`: Enter your total monthly budget for everything minus housing expenses (
          rent / mortgage)
        - `Actual Budget`: Enter your monthly income minus your monthly housing expenses.
    - Miscellaneous Table:
        - `Bi-Monthly Salary`: `adjuftments` assumes you get paid twice a month. Enter your
          take-home bi-monthly salary
        - `Monthly Rent`: Enter your monthly housing expenses (rent / mortgage).
        - `Monthly Starting Balance`: This is the checking balance you would like to begin each new
          month with.
        - `Starting Checking Balance`: Enter your checking balance before entering any new expenses
        - `Starting Savings Balance`: Enter your primary savings balance before entering any new
          expenses
        - `Starting House Balance`: Enter your home savings balance (if applicable) before entering
          any new expenses
        - `Starting Shared Balance`: Enter your shared savings balance (if applicable) before
          entering any new expenses
        - `Employer`: Enter your employer (or comma separated list of employers). Expenses with the
          Transaction formatted: `{{Employer}} - Salary` will be counted towards the monthly
          paycheck count

### Get your API Credentials

1) This part is actually pretty simple. Go to https://airtable.com/account and
   select `Generate API Key`.
2) You also need your new Base ID. It's pretty simple to grab from https://airtable.com/api
3) Add these credentials to the `.env` file

## Splitwise Configuration

### Get your API Credentials / Config Settings

1) Create a new app and API key here: https://secure.splitwise.com/apps/new
    - Set Callback URL as: http://localhost:5000/authorize
2) Collect the following information and enter it into your `.env` file:
    - `Consumer Key`
    - `Consumer Secret`
3) Run the Adhoc Splitwise Credentials Webserver:
    - This requires the docker image from this project. If you haven't already, you can build it
      locally with `docker-compose build api`
    - Run the `splitwise_credentials` webserver
      ```shell
      docker run --rm -it \
        --volume ${PWD}:/home/adjuftments_v2 \
        --publish 5000:5000 \
        --entrypoint  "" \
        adjuftments_v2_api \
        python /home/adjuftments_v2/adjuftments_v2/utils/splitwise_utils/splitwise_credentials.py
      ```
    - Login via Splitwise @ [http://localhost:5000/](http://localhost:5000/)
    - Copy the credentials from the exposed JSON to the `.env` file
4) Identify your Financial Partner
    - Go to [https://secure.splitwise.com/#/friends](https://secure.splitwise.com/#/friends) and
      select your friend from the left side of the page
    - You should be on a new
      URL: [https://secure.splitwise.com/#/friends/<FRIEND ID>](https://secure.splitwise.com/#/friends)
    - Grab the Firend ID from the URL and copy it to your `.env` file

## Pushover Config

- Set up a Pushover account via the
  webpage: [https://pushover.net/signup](https://pushover.net/signup) or via the Android / iOS Apps
  directly. There is a small one-time fee (~ $5), but it is worth it for push notifications!
- Update the `PUSHOVER_PUSH_TOKEN` and `PUSHOVER_PUSH_USER` values in the `.env` file.

## Imgur Config

- Set Up an Imgur Account here: [https://imgur.com/register](https://imgur.com/register)
- Set up an Application
  here: [https://imgur.com/account/settings/apps](https://imgur.com/account/settings/apps)
- Add the Client ID to the `.env` file

## Additional Credentials

- Set up a few other key items on the `.env` file. These will be used for authentication in various
  services:
    - `ADJUFTMENTS_API_TOKEN`
    - `DATABASE_PASSWORD`

* * *
* * *
