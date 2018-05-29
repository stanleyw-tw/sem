import subprocess
import re
from pprint import pformat


class SimulationRunner(object):
    """
    The class tasked with running simulations.
    """

    ##################
    # Initialization #
    ##################

    def __init__(self, path, script):
        """
        Initialization function.
        """

        # Check whether path points to a valid installation
        if subprocess.run(
                "./waf", cwd=path, stdout=subprocess.PIPE).returncode != 0:
            raise ValueError(
                "Path does not point to a valid ns-3 installation")

        # Make sure script is available
        if script not in str(subprocess.run(["./waf", 'list'], cwd=path,
                                            stdout=subprocess.PIPE).stdout):
            raise ValueError(
                "Script is not a valid ns-3 program name")

        # Get the program's executable filename
        # TODO We can do this using build/build-status.py, provided we find a
        # way to link the script name in ns-3 to the correct build-status entry

        self.path = path
        self.script = script

    #############
    # Utilities #
    #############

    def get_available_parameters(self):
        """
        Return a list of the parameters made available by the script.
        """

        # At the moment, we rely on regex to extract the list of available
        # parameters. A tighter integration with waf would allow for a more
        # natural extraction of the information.

        result = subprocess.check_output(['./waf', '--run', '%s --PrintHelp' %
                                          self.script], cwd=self.path).decode(
                                             'utf-8')

        options = re.findall('.*Program\sOptions:(.*)General\sArguments.*',
                             result, re.DOTALL)

        if len(options):
            args = re.findall('.*--(.*?):.*', options[0], re.MULTILINE)
            return args
        else:
            return []

    ######################
    # Simulation running #
    ######################

    def run_simulations(self, parameter_list, verbose=False):
        """
        Run several simulations using a certain combination of parameters.

        Yields results once simulations are completed
        """

        # XXX For now, we use waf to run the simulation. This dirties the
        # stdout with waf's build output.

        for idx, parameter in enumerate(parameter_list):
            if verbose:
                print("\nSimulation %s/%s:\n%s" % (idx+1, len(parameter_list),
                                                   parameter))

            current_result = {}
            current_result.update(parameter)

            command = ' '.join(['--%s=%s' % (param, value) for param, value in
                                parameter.items()])
            command = '%s %s' % (self.script, command)
            execution = subprocess.run(['./waf', '--run', command],
                                       cwd=self.path, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

            if execution.returncode > 0:
                print("Simulation exited with an error. \nStderr: %s\nStdout: %s" % (execution.stderr, execution.stdout))

            current_result['stdout'] = execution.stdout.decode('utf-8')

            yield current_result
