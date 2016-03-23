Requirements:
  * cver, icarus, GHDL or vlog/vcom (default)
  * py.test

See the Makefile - it contains targets per simulator. 


Naming Tests
------------
The tests in this directory are specific to bugs/issues discovered
in a release.  The tests are named after the github issue number
(e.g. 98, 117, etc.).  When adding new bug tests create a github
issue, record the github issue number, and then create a test with
the issue number.  Example of issue and test names:

   117: test_issue_117, https://github.com/jandecaluwe/myhdl/issues/117
   98: test_issue_98, https://github.com/jandecaluwe/myhdl/issues/98
   40: test_issue_40, https://github.com/jandecaluwe/myhdl/issues/40

In many cases there will be large gaps in the issue number because
not all issues are reported bugs (many are enhancement requests) and
github shares enumeration with pull-requests.
