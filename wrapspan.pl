#!/usr/bin/env perl

while(<>) {
	chomp;
	my @words = split;
	next unless @words;
	my @spanwords;
	foreach my $w ( @words ) {
		my @post;
		if( $w =~ /^(\<p\>)(.*)$/ ) {
			push( @spanwords, $1 );
			$w = $2;
		} elsif( $w =~ /^(.*)(\<\/p\>)$/ ) {
                        push( @post, $2 );
                        $w = $1;
                }
		my $punct = '';
		if( $w =~ /^(.*)([[:punct:]])/ ) {
			push( @post, $2 );
			$w = $1;
		}
		my $end = join( '', reverse @post );
		push( @spanwords,
		  sprintf( '<span class="origword">%s</span>%s', $w, $end ) );
	}
	print join( ' ', @spanwords );
}
