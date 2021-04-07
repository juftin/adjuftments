<p align="center">
  <img src="docs/static/juftin.png" width="250" height="250"  alt="juftin logo">
  <img src="docs/static/adjuftments.png" width="500" alt="adjuftments">
</p>

## What is `adjuftments`?

`adjuftments` is a financial application that tracks expenses, income, and more. Ultimately, the
goal of `adjuftments` is to be mindful of spending, and to plan around maximizing savings at the end
of each month. So what makes `adjuftments` different from your Excel spreadsheet? Mainly,
`adjuftments` is built on top of `splitwise` and `airtable`, which helps it do some pretty cool
stuff. Secondly, at any given point during the month you can compare your spending with where you
planned to be, `adjuftments` will help you save money. Lastly, `adjuftments` has a few other handy
features including monthly spending categorization, stock portfolio price syncing, handy
visualizations, and helpful push notifications built on `pushover`.

## What's under the hood?

`adjuftments` has been a personal project of mine for the past few years. It started out as a Google
Sheet with some painful VLOOKUP functions built into it. Today, `adjuftments` is a multi-container
docker application that consists of a few components and services:

- PostgreSQL Database
    - The backend of `adjuftments` is a PostgreSQL database that stays in-sync with the data
      residing in `airtable`. The underlying schema and data structure is built with
      the [SQLAlchemy](https://www.sqlalchemy.org/)
      using the Declarative Base method. These are financial records, so the database is self
      hosted. Data is also persisted inside of `airtable` as well.
- REST API
    - There are no services that connect to the PostgreSQL backend apart from the REST API. This
      REST API is built on top of [Flask](https://flask.palletsprojects.com/), requires
      authorization using an API token embedded in headers, and uses Gunicorn as the underlying WSGI
      Engine with multiple workers.
- API Python Wrapper
    - To access the REST API, a Python Wrapper was built around it with
      the [requests](https://docs.python-requests.org/) module. The primary data refresh service is
      built around this wrapper. This service checks for new/updated data from `airtable`
      and `splitwise` and publishes the latest aggregate dashboard which tracks things like monthly
      spending, bank account balances, and projected savings.
- Job Scheduler
    - Also using the REST API wrapper, `adjuftments` has a job scheduling service that performs
      scheduled tasks like updating stock prices, refreshing published images, performing
      maintenance on the database, etc. These tasks are scheduled as using
      the [APScheduler](https://apscheduler.readthedocs.io/en/stable/) service.

## How does `adjuftments` integrate with `airtable`?

`adjuftments` is built on top of airtable, every expense that you import into the application is
actually a record inside of `airtable`. This allows a couple of cool things:

- Record Access: At any time you can go back and modify, delete, or create historic expenses.
  `airtable` has mobile apps, and a responsive WebUI that makes data management easy.
- Record Entry: Creating new expenses is really easy using `airtable`'s native form functionality.

## How does `adjuftments` integrate with `splitwise`?

`adjuftments` performs a two way sync with records in `splitwise`. This means that after you
designate a financial partner (a friend in Splitwise and someone who you share expenses with), you
can create Splitwise expenses directly from `adjuftments`, and also auto sync with expenses created
inside of `splitwise`. Your ongoing balance with your financial partner is also tracked.

## How do I set up `adjuftments` for myself?

`adjuftments` set up is relatively straightforward. All credentials are set using
a [`.env`](example.env) file. Inside of this `.env`
file you will store information like your timezone, local directory path, and API credentials to the
various services `adjuftments` integrates with:

- `airtable`: frontend and data management
- `splitwise`: expense sharing integration
- `imgur`: temporary image hosting intermediary
- `pushover`: mobile push notifications

More details on the initial setup can be found in
the [documentation](docs/configuration/initial_setup.md). Once the `.env` file has been configured,
the entire project

## This seems like an awful lot of trouble to keep track of expenses

Nope.

* * *

* * *

<br/>
<br/>
<br/>

###### Cool stuff happens in Denver, CO [<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Flag_of_Denver%2C_Colorado.svg/800px-Flag_of_Denver%2C_Colorado.svg.png" width="25" alt="Denver">](https://denver-devs.slack.com/)