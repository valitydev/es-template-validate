* Create file <i><template_name>.json</i> and fill it with ES index template
* Copy <i><template_name>.json</i>  into <i>templates</i> directory
* Create file <i><template_name>.json</i> and fill it with sample data for your <i><template_name></i>  
* Copy <i><template_name>.json</i>  into <i>samples</i> directory

* Build and run ES container:<br>
<code>docker-compose up -d</code>

* Run app.py script and read it's output:<br>
<code>python app.py</code>

If ES-generated mapping matches your template script will exit with 0 status code or 1 in opposite case.