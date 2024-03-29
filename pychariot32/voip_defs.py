# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:06:27 2021
This include file contains the constants, typedefs and base definitions
for application programming for VoIP functionality.

brief       Base VoIP definitions.

Copyright (c) 2004-2006 Ixia. All rights reserved.

/***************************************************************
 *
 *  For more information, contact:
 *
 *  Ixia
 *  26601 W. Agoura Rd.
 *  Calabasas, CA 91302 USA
 *  Web:   http://www.ixiacom.com
 *  Phone: 818-871-1800
 *  Fax:   818-871-1805
 *
 *  General Information:
 *    e-mail: info@ixiacom.com
 *
 *  Technical Support:
 *    e-mail: support@ixiacom.com
 *
 ***************************************************************/
@author: haoyue
"""

### Definition of a unique signature, characterizing an ASD of type VoIP.
### Used when instantiating ASD objects.

IX_VOIP_ASD_TYPE_UUID                     = "eef7b8d5-d249-45e5-8179-b4cf1d0605e8"


### ASD subtypes that are handled by ASE VoIP.
### When adding new types, be sure to updated IX_VOIP_ASD_TYPE_COUNT below.

IX_VOIP_ASD_TYPE_VOIP                     = 0
IX_VOIP_ASD_TYPE_COUNT                    = 1


### VoIP Codecs
### These are guaranteed to be contiguous in value.

# IX_VOIP_CODEC
IX_VOIP_CODEC_NONE                              = 1
IX_VOIP_CODEC_G711u                             = 2
IX_VOIP_CODEC_G723_1A                           = 3
IX_VOIP_CODEC_G723_1M                           = 4
IX_VOIP_CODEC_G729                              = 5
IX_VOIP_CODEC_G711a                             = 6
IX_VOIP_CODEC_G726                              = 7
IX_VOIP_CODEC_AMR_NB_4_75                       = 8
IX_VOIP_CODEC_AMR_NB_5_15                       = 9
IX_VOIP_CODEC_AMR_NB_5_9                        = 10
IX_VOIP_CODEC_AMR_NB_6_7                        = 11
IX_VOIP_CODEC_AMR_NB_7_4                        = 12
IX_VOIP_CODEC_AMR_NB_7_95                       = 13
IX_VOIP_CODEC_AMR_NB_10_2                       = 14
IX_VOIP_CODEC_AMR_NB_12_2                       = 15
IX_VOIP_CODEC_AMR_WB_6_6                        = 16
IX_VOIP_CODEC_AMR_WB_8_85                       = 17
IX_VOIP_CODEC_AMR_WB_12_65                      = 18
IX_VOIP_CODEC_AMR_WB_14_25                      = 19
IX_VOIP_CODEC_AMR_WB_15_85                      = 20
IX_VOIP_CODEC_AMR_WB_18_25                      = 21
IX_VOIP_CODEC_AMR_WB_19_85                      = 22
IX_VOIP_CODEC_AMR_WB_23_05                      = 23
IX_VOIP_CODEC_AMR_WB_23_85                      = 24


### Map the first and last codec, trust they are
### contiguous and use the definitions below for
### index arithmetic.
### BEGIN is the start of the codec list, inclusive
### END   is the end of the codec list, exclusive
###       END points to the first invalid position
###       after the last codec.
IX_VOIP_CODEC_BEGIN                     = IX_VOIP_CODEC_G711u
IX_VOIP_CODEC_END                       = IX_VOIP_CODEC_AMR_WB_23_85 + 1
IX_VOIP_CODEC_COUNT                     = IX_VOIP_CODEC_END-IX_VOIP_CODEC_BEGIN
IX_VOIP_HPP_CODEC_END                   = IX_VOIP_CODEC_G726 + 1
IX_VOIP_HPP_CODEC_COUNT                 = IX_VOIP_HPP_CODEC_END - IX_VOIP_CODEC_BEGIN


### Max and min permittable values for VoIP parameters.

IX_VOIP_IPV4                                    = 4
IX_VOIP_IPV6                                    = 6

# IPv6: FEDC:BA98:7654:3210:FEDC:BA98:7654:3210
IX_VOIP_IP_ADDRESS_LENGTH                       = 40

IX_VOIP_INTER_DATAGRAM_GAP_MIN                  = 1
IX_VOIP_INTER_DATAGRAM_GAP_DEFAULT              = 10
IX_VOIP_INTER_DATAGRAM_GAP_MAX                  = 200

IX_VOIP_CONCURRENT_VOICE_STREAM_MIN             = 1
IX_VOIP_CONCURRENT_VOICE_STREAM_DEFAULT         = 10
IX_VOIP_CONCURRENT_VOICE_STREAM_MAX             = 2147483647

IX_VOIP_SRC_PORT_MIN                            = 1
IX_VOIP_SRC_PORT_DEFAULT                        = 1024
IX_VOIP_SRC_PORT_MAX                            = 65535


IX_VOIP_DST_PORT_MIN                            = 1
IX_VOIP_DST_PORT_DEFAULT                        = 16384
IX_VOIP_DST_PORT_MAX                            = 65535

DELAY_MINIMUM                                   = 10
DELAY_MAXIMUM                                   = 200
ACTIVITY_RATE_MINIMUM                           = 1
ACTIVITY_RATE_MAXIMUM                           = 100
INITIAL_DELAY_MINIMUM                           = 0
INITIAL_DELAY_MAXIMUM                           = 2147483647
ADDITIONAL_DELAY_MINIMUM                        = 0
ADDITIONAL_DELAY_MAXIMUM                        = 300
TR_DURATION_MINIMUM                             = 1
TR_DURATION_MAXIMUM                             = 3600
PORT_MINIMUM                                    = 1
PORT_MAXIMUM                                    = 65535
JITTER_BUFFER_MILLISECONDS_MINIMUM              = 10
JITTER_BUFFER_MILLISECONDS_MAXIMUM              = 1600
JITTER_BUFFER_DATAGRAMS_MINIMUM                 = 1
JITTER_BUFFER_DATAGRAMS_MAXIMUM                 = 8
FRAMES_PER_DG_MINIMUM                           = 1
FRAMES_PER_DG_MAXIMUM                           = 10000
VARIABLE_RATE_MAX                               = 4294967295
RTP_PAYLOAD_MINIMUM                             = 0
RTP_PAYLOAD_MAXIMUM                             = 127
