/****************************************************************************
 *
 *   Copyright (C) 2013-2016 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

/* Auto-generated by genmsg_cpp from file adc_report.msg */


#include <inttypes.h>
#include <px4_platform_common/log.h>
#include <px4_platform_common/defines.h>
#include <uORB/topics/adc_report.h>
#include <uORB/topics/uORBTopics.hpp>
#include <drivers/drv_hrt.h>
#include <lib/drivers/device/Device.hpp>

constexpr char __orb_adc_report_fields[] = "uint64_t timestamp;uint32_t device_id;int32_t[12] raw_data;uint32_t resolution;float v_ref;int16_t[12] channel_id;uint8_t[4] _padding0;";

ORB_DEFINE(adc_report, struct adc_report_s, 92, __orb_adc_report_fields, static_cast<uint8_t>(ORB_ID::adc_report));


void print_message(const adc_report_s &message)
{

	PX4_INFO_RAW(" adc_report_s\n");

	const hrt_abstime now = hrt_absolute_time();

	if (message.timestamp != 0) {
		PX4_INFO_RAW("\ttimestamp: %" PRIu64 "  (%.6f seconds ago)\n", message.timestamp, (now - message.timestamp) / 1e6);
	} else {
		PX4_INFO_RAW("\n");
	}
	char device_id_buffer[80];
device::Device::device_id_print_buffer(device_id_buffer, sizeof(device_id_buffer), message.device_id);
PX4_INFO_RAW("\tdevice_id: %d (%s) \n", message.device_id, device_id_buffer);
	PX4_INFO_RAW("\traw_data: [%" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 ", %" PRId32 "]\n", message.raw_data[0], message.raw_data[1], message.raw_data[2], message.raw_data[3], message.raw_data[4], message.raw_data[5], message.raw_data[6], message.raw_data[7], message.raw_data[8], message.raw_data[9], message.raw_data[10], message.raw_data[11]);
	PX4_INFO_RAW("\tresolution: %" PRIu32 "\n", message.resolution);
	PX4_INFO_RAW("\tv_ref: %.4f\n", (double)message.v_ref);
	PX4_INFO_RAW("\tchannel_id: [%d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d]\n", message.channel_id[0], message.channel_id[1], message.channel_id[2], message.channel_id[3], message.channel_id[4], message.channel_id[5], message.channel_id[6], message.channel_id[7], message.channel_id[8], message.channel_id[9], message.channel_id[10], message.channel_id[11]);
	
}
