Analyzer of differences between properties in different environments in the XL Deploy repository.

In an ideal situation each environment which you deploy to, is identically configured. This:
- minimizes the number of environment specific changes that are required.
- minimizes the need for environment specific variables.
- minimizes the chance that the application is incorrectly configured.
however, in the real world, XL Deploy is used to iron out all the differences between the environments and people might be overwhelmed by the sheer number of properties
 (you can't see the trees for the wood)

This tool will help you to quickly detect potential problems in the environment configuration. It generates an HTML report,
which gives you a colorful review of the current status.  

color coding scheme
===================
This program analyses the value of a property in a specific environment, and compares it to all the value in all other environments. Depending on the result
you one of three different colors:
- green: the values are different in each environment
- orange: the values are the same in each environment
- red: some environments have the same value 

When the color is green, we can conclude this is a real environment specific property. For URLs and IP addresses consider minimizing this by using a (DNS) naming scheme.
When the color is orange, you can ask yourself if the property is really necessary. Consider removing it in order to reduce the number of variables you have to manage.
When the color is red, this potentially indicates a problem in the configuration as some environments have the same value. You may have the same password in different environment, or be pointing to the same backend system.

how to run
==========
assuming you have a unix system :-) Basically you have to point to two or more environments that you want to compare.

``` bash
export PATH=$PATH:$DEPLOYIT_CLI_HOME/bin
cli.sh -username admin \
	-password admin \
	-f $(pwd)/analyze-environments \
	-- \
	--output $(pwd)/app-environment-analysis.html \
	/Environments/app/{dev,test,qa,prod}
```
