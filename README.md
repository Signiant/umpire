# Umpire Dependency Manager

Umpire is a Python-based generic dependency resolver which aims to be platform agnostic, extensible, and simple to use.

Umpire was developed as an easy to install command line tool, with it's flexibility being derived from the JSON file options.

Umpire reads a JSON file to retrieve, cache, and link files to their appropriate destination from an Amazon S3 backed repository of compressed packages.

## Installation

Umpire is available as a [pip package]((https://pypi.python.org/pypi/pip), and requires Python 2.7.15.

To install Umpire from the command line:

```
$ pip install umpire
```

## Examples

Below is an example deployment JSON file. The URL is composed of the identifier (s3://) and the bucket name. When using an authenticated bucket, the user must have either the AWS\_ACCESS\_KEY\_ID and AWS\_SECRET\_ACCESS\_KEY variables set or a properly configured credentials file for your platform.

The items array contains the list of dependencies. Each one requires a platform, name and version. In the s3 bucket they need to be stored with the prefix: **$PLATFORM/$NAME/$VERSION**. Umpire does a case insensitive match against this naming convention to find the appropriate dependency. It will download all files matching the prefix in the bucket, and will attempt to unpack them for future deployment.

There's also a couple of other options that you can specify. They are:

**link**: [true/false] -- Specifies whether Umpire should link the dependency files to the destination or copy them. Default true.

**keep_updated**: [true/false] -- Specifies whether Umpire should check with the remote S3 bucket when run to see if the dependency has been changed. Default false.

```
[
     {
         "url":"s3://umpire-test/",
         "items":[
             {
                 "name":"test",
                 "version":"test_tgz",
                 "platform":"test",
                 "keep_updated":true,
                 "link":false,
                 "destination":"$ENVIRONMENT_VARIABLE/destination"
             },
             {
                 "name":"test",
                 "version":"test_zip",
                 "platform":"test",
                 "keep_updated":true,
                 "destination":"./destination"
             }
         ]
     }
 ]
```

## Contributing

Want to help out?

We'll gladly take any help in bug fixes, or feature updates if it fits within our whole vision of Umpire. Feel free to create a fork of the repository, and submit a pull request if you do anything cool.

## Todos

 - Publishing support
 - Bzip support
 - Optional unpacking
 - File exclusion

## License
----

Umpire is licensed under the [MIT license](https://github.com/Signiant/umpire/blob/develop/LICENSE)
