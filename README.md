[![Build Status](https://travis-ci.com/BrandwatchLtd/api_sdk.svg?branch=master)](https://travis-ci.com/BrandwatchLtd/api_sdk)

# Brandwatch API SDK

## Introduction

The Brandwatch API SDK was designed to address many of the challenges involved in building complex applications which interact with RESTful API's in general and Brandwatch's API from Python 3, in particular:

- The SDK's object hierarchy roughly mirrors the API's resource hierarchy, making the code intuitive for those familiar with the Brandwatch platform
- All required parameters are enforced, and most optional parameters are supported and documented
- Typical Brandwatch workflows are supported behind the scenes; for instance, one can validate, upload, and backfill a query with a single function call
- The SDK is designed to support simple and readable code: sensible defaults are chosen for rarely used parameters and all resource IDs are handled behind the scenes

From the user's perspective, the basic structure of the SDK is as follows.  One first creates an instance of the class `BWProject`; this class handles authentication (via a user name and password or API key) and keeps track of project-level data such as the project's ID.  (Behind the scenes, the user-level operations are handled by the class `BWUser` from which `BWProject` is inherited.)  One passes `BWProject` instance as an argument in the constructor for a series of classes which manage the various Brandwatch resources: queries, groups, tags, categories, etc.  These resource classes manage all resource-level operations: for example a single `BWQueries` instance handles all HTTP requests associated with queries in its attached project. 

## Installation

Be sure to install the latest version of Python 3.x. You can install bwapi on your machine by running the following command:

`pip install bwapi`

This allows you to run scripts that import bwproject or bwresources from anywhere on your computer. 

## Examples

Please see the Jupyter notebook DEMO.ipynb for examples.  This notebook was built as a beginner's guide to using the Brandwatch API SDK, so it has example code, as well as detailed instructions for use.

## Disclaimer

This is not an official or supported Brandwatch library, and should be implemented at the users' own risk. 
