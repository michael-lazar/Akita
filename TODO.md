## Future Improvements

- Add more statistics to the dashboard: HTTP status codes (especially 5xx codes), request IP addresses, user-agents.
- Extend the HTTP log reader to support customizable, non-standard log formats.
- Make all of the statistics and refresh rates configurable.
- Add a configuration file @ **{HOME}/.config/akita/akita.conf**.
- Save traffic alerts in a log file or HTML document.
- Re-write the logfile reader/parser thread in C to improve performance.
- Consider switching to an async library instead of using threads.

To extend this application to work with distributed web servers, we would need to setup a client-server architecture.
Each machine would run a lightweight client to aggegate metrics from a single log file, and publish events to the
server at regular intervals. Similar to the [statsd](https://github.com/etsy/statsd) daemon.
[Kismet](https://www.dd-wrt.com/wiki/index.php/Kismet_Server/Drone) is another example of a terminal program that operates
with a client-server model.

## Things that still need to be tested

- Different environments (``LOCALE``, ``LANG``, ``TERM``) and terminals (iterm, xterm, gnome-terminal, etc.)
- Curses handling of unicode wide characters and emojis.
- Corrupt or non-``UTF-8`` encoded log files, could utilize a fuzzing tool like [Hypothesis](https://github.com/HypothesisWorks/hypothesis-python).
- How server log-rotation behavior effects the application.
- Benchmarking performance and observing what happens when we can't keep up with the stream of log messages.
