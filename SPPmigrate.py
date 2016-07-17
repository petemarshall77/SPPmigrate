#!/usr/bin/python

# Migrate SPP repositories
#
#   Usage: SPPmigrate <source-directory> <target-directory>
#
#   Copy the contents of source-directory, including all sub-directories
#   to target-directory.
#
#   In additional to copying the files, MD5 checksums are created, checked
#   and logged for auditing purposes. The process also checkpoints its
#   progress to allow for restarts if necessary

from __future__ import print_function
import hashlib, binascii, subprocess, sys, os, time

class tee:
    """
    Object that writes output to two file descriptiors. Achieves the same result
    as the 'tee' command but allows user interactivity
    """
    def __init__(self, _fd1, _fd2):
        self.fd1 = _fd1
        self.fd2 = _fd2

    def __del__(self):
        if self.fd1 != sys.stdout and self.fd1 != sys.stderr:
            self.fd1.close()
        if self.fd2 != sys.stdout and self.fd2 != sys.stderr:
            self.fd2.close()

    def write(self, text):
        self.fd1.write(text)
        self.fd2.write(text)

    def flush(self):
        self.fd1.flush()
        self.fd2.flush()


def query_yes_no(question):
    """
    Very simple yes/no checker. Write out question and get a 'y' or
    'n' as a response. Return that response.
    """
    while True:
        sys.stdout.write(question+' ')
        response = raw_input().lower()[0]
        if response in ['y', 'n']:
            return response
        else:
            print("Please respond y or n")


def checksum_md5(filename):
    """
    Return the MD5 checksum of a given file as a string
    """
    md5 = hashlib.md5()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(md5.block_size*128), b''): 
            md5.update(chunk)
    return binascii.hexlify(md5.digest()).decode('utf-8')


def copy_file(source, target):
    """
    Copy the (fully qualified path/filename) to the (full qualified
    path/filename. Spawn the ditto command to do the actual copy as
    we're on MAC OS.
    If the copy works, check the MD5 values agree. Return True or False
    """
    sys.stdout.write("Copying: %s to %s. " % (source, target))
    try:    
        subprocess.check_call(["ditto", source, target])
    except subprocess.CalledProcessError as e:
        print("FAILED - OS copy failed")
        return False
    else:
        src_md5 = checksum_md5(source)
        tgt_md5 = checksum_md5(target)
        if src_md5 == tgt_md5:
            print("OK. Checksum: %s" % src_md5)
            return True
        else:
            print("FAILED - Checksum mismatch: Source: %s, Target: %s" %
                  (src_md5, tgt_md5))
            return False


def copy_dir(source, target):
    """
    Copy all files and subdirectories in the source directory to
    the target directory. Note: this does not copy sub-directories
    """
    print("Copying %s to %s" % (source, target))
    file_count = 0
    error_count = 0
    for file_name in os.listdir(source):
        if os.path.isfile(os.path.join(source, file_name)):
            file_count += 1
            if copy_file(os.path.join(source, file_name),
                         os.path.join(target, file_name)) == False:
                error_count += 1

    # File count is zero? No files in directory: create it.
    if file_count == 0:
        print("Creating empty directory:", target)
        os.mkdir(target)

    return(file_count, error_count)


def do_copy(source, target):
    """
    Generate a list of all the subdirectories in <source> with corresponding
    <target> names and call copy_dir on each pair.
    """
    # Get source list
    tree = [directory for directory in os.walk(source)]
    source_root = os.path.abspath(tree[0][0])
    source_list = [(os.path.abspath(directory[0]), len(directory[2])) for directory in tree]
    
    # Print out source details and check user wants to continue
    print("Source directory:", source_root)
    print("Found", len(source_list), "directories...")
    file_count = 0
    for directory in source_list:
        print(directory[0], directory[1], "files")
        file_count += directory[1]
    print("Total", file_count, "files.")
    if query_yes_no('Continue? [y|n]') == False:
        return(0,0)

    # Add targets for create copy list
    target_root = os.path.abspath(target)
    copy_list = [ (directory[0],
                   os.path.join(target_root, os.path.relpath(directory[0],source_root)))
                  for directory in source_list]

    # Print out copy list and check user wants to continue
    print("Target directory:", target_root)
    for entry in copy_list:
        print("Will copy", entry[0], "to", entry[1])
    if query_yes_no('Continue? [y|n]') == False:
        return(0,0)

    # All set, do the copy
    file_count = 0
    error_count = 0
    for (source, target) in copy_list:
        (files, errors) = copy_dir(source, target)
        print("Directory copied.", files, "files,", errors, "errors.")
        print() # blank line
        file_count += files
        error_count += errors

    return(file_count, error_count)

def do_main():
    """
    Start here. Say hello and check the user has specified a source and target.
    """
    print("SPPmigrate:", time.asctime())
    if len(sys.argv) != 3:
        print("Usage is: SPPmigrate <source-directory> <target-directory>")
        return(1)

    # Open a log file and tee the output to it
    stdout_save = sys.stdout
    logfilename = "SPPmigrate_" + time.asctime() + ".log"
    logfile = open(logfilename, 'w')
    sys.stdout = tee(stdout_save, logfile)

    # All good: let's do it...
    (files, errors) = do_copy(sys.argv[1], sys.argv[2])
    print("All done.", files, "files copied.", errors, "errors.") 


if __name__ == "__main__":
    do_main()
    
    
    
            
