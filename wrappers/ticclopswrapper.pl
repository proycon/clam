#! /usr/bin/perl

use Getopt::Std;

# OPTIONS
#getopts('a:b:c:d:e:f:l:s:t:w:');
getopts('a:b:c:d:e:l:s:t:w:');

$ROOTDIR = $ARGV[0];
$INPUTDIR = $ARGV[1];
$OUTPUTDIR = $ARGV[2];
$STATUSFILE = $ARGV[3];

# a : minfrq
# b : maxfrq
# c : minwordlength
# d : maxwordlength
# e : edit/Levenshtein distance
# f : extension of input files
# l : lexicon
# t : top n best-ranking
# w : switches (evaluation, conversion, debugging

# defaults: set $opt_X unless already defined (Perl Cookbook p. 6):
#$opt_b ||= ' ';
#$opt_e ||= '\n';
#$opt_r ||= 0;
#$opt_l ||= 'ned';
#$opt_d ||= '';

#PARTICCL: $maxfrq, $minfrq, $minwlength, $maxwlength)
$P5 = $opt_b . '-' . $opt_a . '-' . $opt_c . '-' . $opt_d;

$opt_w =~ s/,//g;

#Output filename is static for now (proycon)
$ops_s = 'output'; 

#$switches = 'vrdxLYVSRN' . $opt_e . $opt_w;
$switches = 'vrsLYVSRN' . $opt_e . $opt_w; 


$lexicon = "$INPUTDIR/lexicon.lst"

#if ($opt_l =~ /contemp/){
#    $lexicon = $ROOTDIR . '/data/int/ARG4.SGDLEX.isolat1.TICCL.v.4.lst';
#}
#elsif ($opt_l =~ /hist/){
#    $lexicon = $ROOTDIR . '/data/int/ARG4.SGDLEX.GB1914.isolat1.TICCL.v.4.lst';
#}
#elsif ($opt_l =~ /none/){
#    $lexicon = $ROOTDIR . 'empty.lst';
#}
#else {
#    print "NOT DEFINED\n";
#}

#$ARGUMENTS = $INPUTDIR . ' ' . $opt_f . ' ' . "$OUTPUTDIR\/$opt_s" . '.options' . $switches . '.foci' . $P5 . '.rank' . $opt_t . '.' . ' ' . $lexicon . ' ' . $P5 . ' ' . 'ispell:/son/KBDATA/IspellDict/dutch96 /son/PARTICCL/BUILDALPH/ARG7.DDD.VOLK.evalinput.v04.SEL.NOSPLITS.DIAC.lst /son/KB-TICCL/PRODv2/ARG8.charmap.rewrit.6classes.lst /son/PARTICCL/SGDLEX/ARG9.SGDLEX.isolat1.P5.numsort.hash.allupto2to2.CONFUSIONINDEXMATRIX.ticcl2.lst /son/PARTICCL/BUILDALPH/PARTICCL.buildalphabet.P5.upper3digit2punct.nonull.nospace.LC.numsort.1to2and2to2.lst' . ' ' . $opt_t;
#$ARGUMENTS = $INPUTDIR . '#' . $OUTPUTDIR . ' ' . '\.' . ' ' . "$OUTPUTDIR/$opt_s" . ' ' . $switches . ' ' . $lexicon . ' ' . $P5 . ' ' . 'ispell:/son/KBDATA/IspellDict/dutch96 /son/PARTICCL/Martinet/Martinet.TICCLops.GS.v01.utf8.txt /son/KB-TICCL/PRODv2/ARG8.charmap.rewrit.6classes.lst /son/PARTICCL/SGDLEX/ARG9.SGDLEX.isolat1.P5.numsort.hash.allupto2to2.CONFUSIONINDEXMATRIX.ticcl2.lst /son/PARTICCL/BUILDALPH/PARTICCL.buildalphabet.P5.upper3digit2punct.nonull.nospace.LC.numsort.1to2and2to2.lst' . ' ' . $opt_t . ' ' . $STATUSFILE;

$ARGUMENTS = $INPUTDIR . '#' . $OUTPUTDIR . ' ' . '\.' . ' ' . "$OUTPUTDIR/$opt_s" . ' ' . $switches . ' ' . $lexicon . ' ' . $P5 . ' ' . 'ispell:'.$ROOTDIR.'/data/ext/dutch96 ' . $ROOTDIR . '/data/int/Martinet.TICCLops.GS.v01.utf8.txt ' . $ROOTDIR.'/data/int/ARG8.charmap.rewrit.6classes.lst ' . $ROOTDIR . '/data/int/ARG9.SGDLEX.isolat1.P5.numsort.hash.allupto2to2.CONFUSIONINDEXMATRIX.ticcl2.lst ' . $ROOTDIR . '/data/int/PARTICCL.buildalphabet.P5.upper3digit2punct.nonull.nospace.LC.numsort.1to2and2to2.lst' . ' ' . $opt_t . ' ' . $STATUSFILE;

#`perl /son/PARTICCL/parTICCL.273.P5.pl $ARGUMENTS`;
#$donetime = time();
open (STATUS, ">>$STATUSFILE");
#print STATUS "EPOCH TIME: $donetime\n";
#print STDERR "EPOCH TIME1: $donetime\n";
    #$mtime = (stat($STATUSFILE))[9];
    #print STDERR "MTIME1: $mtime\n";
$pid = open(README, " perl $ROOTDIR/TICCLops.pl $ARGUMENTS |")  or die "Couldn't fork: $!\n";
while (<README>) {
    #$gonetime = time();
    #$lapse = $gonetime - $donetime;
    #if ($lapse == 20){
        #$donetime = $gonetime;
        #$count++;
        #print STATUS "SEENTWENTYSECONDS $count TIMES\n";
    #}
    #$mtime = (stat(STATUS))[9];
    #$mtime = (stat($STATUSFILE))[9];
    #$nowtime = time();
    #$difftime = $nowtime - $mtime; 
    #print STDERR "MTIME: $mtime\n";
    #if ($difftime =~ /20/){
    #$count++;
    #print STATUS "SEENTWENTYSECONDS $count TIMES\n";
    #$mtime = ();
    #}
}
close(README) or die "Couldn't close: $!\n";
close(STATUS);
