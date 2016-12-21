"""
Hacky script to connect to a named docker container that's running some
process and track its log output for things. Helps to sequence services
that take some time to boot/provision.

..

    $ python wait-for.py --help
    $ python wait-for.py \
        --name="my-container"
        --timeout=60 \
        --sleep=1 \
        --verbose \
        --monitor \
        "this thing I'm looking for" \
        "this other things I'm looking for"


Will fail if "this thing I'm looking for" isn't spotted in the container logs
within 60 seconds of starting, it'll check every 1 second. If it fails
it will dump the captured log output to stdout for inspection.

Adding `--monitor` will print the last 2 lines of logs instead of a full stop.

Timeouts can be disabled by setting it to zero or lower.

"""
import click
import re
import time
import docker
from docker.errors import NotFound


def wait_for(container, pattern, timeout=60, sleep=1,
             verbose=False, monitor=False):
    time_spent = 0
    click.secho("\n%s: " % (pattern,), fg='blue', nl=False)
    while True:
        logs = container.logs().decode('utf-8').rstrip()
        if re.findall(pattern, logs):
            break
        time.sleep(sleep)
        if monitor:
            click.secho('\n'.join(logs.split('\n')[-2:]), fg='yellow')
        else:
            click.secho(".", fg="green", nl=False)
        time_spent += sleep
        if timeout > 0 and time_spent > timeout:
            click.secho(".", fg="red")
            if verbose:
                click.echo(logs, err=True)
            raise click.ClickException(
                'Timeout of %s reached for %s' % (timeout, container.name,))
    return True


@click.command()
@click.option("--name", type=click.STRING,
              help="Which container to wait for")
@click.option("--timeout", type=click.INT,
              help="How long to wait for.",
              default=60)
@click.option("--sleep", type=click.INT,
              help="How long to sleep for in between checking",
              default=1)
@click.option("--verbose/--no-verbose",
              help="Log the stdout captured on timeout.",
              default=False)
@click.option('--monitor/--no-monitor',
              help='Print the last line of log output every sleep interval',
              default=False)
@click.argument("patterns", type=click.STRING, nargs=-1)
def cmd(name, timeout, sleep, verbose, monitor, patterns):
    client = docker.from_env()
    try:
        container = client.containers.get(name)
    except NotFound:
        raise click.ClickException('Container %s does not exist.' % (
            name,))

    for pattern in patterns:
        wait_for(container, pattern,
                 timeout=timeout, sleep=sleep,
                 verbose=verbose, monitor=monitor)


if __name__ == '__main__':
    cmd()
