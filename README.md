#Umpire

Umpire is a generic dependency resolver which aims to be both platform agnostic, and downright simple to use. It is developed in Python and is easily extensible.

Using an S3 backed repository of compressed packages, Umpire reads a simple JSON file to retrieve, cache, and link files to their appropriate destination. It's original use case was to keep binary artifacts and tools out of git repositories, but still provide a way for these binaries to be versioned.

Umpire is being developed as an easy to install command line tool, with it's flexibility being derived from the JSON file options.

### Installation
Installing Umpire is easy. All you need is the pip package manager, and Python version 2.7.x (Windows **requires** version **2.7.11**).

```
$ pip install umpire
```

Don't have pip? Get it [here.](https://pypi.python.org/pypi/pip)

### Examples

Below is an example deployment JSON file. The URL is composed of the identifier (s3://) and the bucket name. When using an authenticated bucket, the user must have either the AWS\_ACCESS\_KEY\_ID and AWS\_SECRET\_ACCESS\_KEY variables set or a properly configured credentials file for your platform.

The items array contains the list of dependencies. Each one requires a platform, name and version. In the s3 bucket they need to be stored with the prefix: **$PLATFORM/$NAME/$VERSION**. Umpire does a case insensitive match against this naming convention to find the appropriate dependency. It will download all files matching the prefix in the bucket, and will attempt to unpack them for future deployment.

There's also a couple of other options that you can specify. They are:

**link**: [true/false] -- Specifies whether umpire should link the dependency files to the destination or copy them. Default true.

**keep_updated**: [true/false] -- Specifies whether umpire should check with the remote S3 bucket when run to see if the dependency has been changed. Default false.

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

### Development

Want to help out? Awesome!

We'll gladly take any help in bug fixes, or feature updates if it fits within our whole vision of Umpire. Feel free to create a fork of the repository, and submit a pull request if you do anything cool.

##### Todos

 - Publishing support
 - Bzip support
 - Optional unpacking
 - File exclusion

License
----

Umpire is licensed under the [MIT license](https://github.com/Signiant/umpire/blob/develop/LICENSE)
