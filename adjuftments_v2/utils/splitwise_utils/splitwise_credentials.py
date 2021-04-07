#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Simple Flask Server to Expose Credentials
"""

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from splitwise import Splitwise

from adjuftments_v2.config import SplitwiseConfig

app = Flask(__name__)
app.secret_key = "RandomSecretString"


@app.route("/")
def home():
    if 'access_token' in session:
        return redirect(url_for("credentials"))
    return render_template("home.html")


@app.route("/login")
def login():
    splitwise_object = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                                 consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET)
    url, secret = splitwise_object.getAuthorizeURL()
    session['secret'] = secret
    return redirect(url)


@app.route("/authorize")
def authorize():
    if 'secret' not in session:
        return redirect(url_for("home"))
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    splitwise_object = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                                 consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET)
    access_token = splitwise_object.getAccessToken(oauth_token, session['secret'], oauth_verifier)
    session['access_token'] = access_token
    return redirect(url_for("credentials"))


@app.route("/credentials")
def credentials():
    credential_dict = dict(SPLITWISE_CONSUMER_KEY=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                           SPLITWISE_CONSUMER_SECRET=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                           SPLITWISE_OAUTH_TOKEN=session["access_token"]["oauth_token"],
                           SPLITWISE_OAUTH_SECRET=session["access_token"]["oauth_token_secret"])
    return jsonify(credential_dict)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
