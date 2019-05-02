## Garbage Collection Argo ML

When using argo for Machine Learning, you can run into a problem of a number of pods left after successfully competing. You may have different workflow types that require the pods to persist for different lengths of time for whatever reason. This utility allows you deploy an easy cronjob that will clean up old pods depending on the criteria you set.

Here is an example of deleting all the [scheduled workflows](link to cron workflows) that are over 10 days old

```bash
python gc_cleanup.py --label_selector cronWorkflow --max_age_hrs 240
```

And then to clear out all the non-labeled "adhoc" workflows

```bash
python gc_cleanup.py --label_selector cronWorkflow --max_age_hrs 240 --adhoc
```
**If you do not include the labels and starts_with lists when specifying adhoc, they will be deleted since adhoc is not an actual labeled workflow or type of workflow**


optional arguments:

  -n NAMESPACE, --namespace NAMESPACE
  The custom resource's namespace. The default is "default"
  -grp GROUP, --group GROUP
  The custom resource's group name. The default is "argoproj.io"
  -version VERSION
  The custom resource's version. The default is "v1alpha1"
  -p PLURAL, --plural PLURAL
  The custom resource's plural name to filter by. for example Workflow would be workflows. The default is "workflows"
  --starts_with STARTS_WITH [STARTS_WITH ...]
  A list of specific names filtering for workflows that start with
  --label_selector LABEL_SELECTOR [LABEL_SELECTOR ...]
  A list of labels to filter by
  --adhoc               
  This flag will cause the workflows filtered by the label_selector and starts_with to be ignored if set
  --max_age_hrs MAX_AGE_HRS
  The maximum age to keep workflows for in hours. Default is 168
