#!/usr/bin/env python

"""
simple_switch_13.py - Simple OpenFlow 1.3 L2 learning switch implementation

This module provides a basic OpenFlow 1.3 switch application that implements
L2 learning switch functionality. It learns MAC addresses from incoming packets
and installs flow entries to forward packets to the correct ports.

This application is designed to work with RYU controller and can be used as a
starting point for more complex SDN applications.
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib import hub
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.lib.packet import ether_types


class SimpleSwitch13(app_manager.RyuApp):
    """Simple OpenFlow 1.3 L2 learning switch application."""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        # Initialize MAC address table for each datapath
        self.mac_to_port = {}
        # Initialize topology information
        self.topology_api_app = self
        self.switches = {}
        self.links = {}
        self.hosts = {}
        
        # Start a thread to periodically print switch statistics
        self.monitor_thread = hub.spawn(self._monitor)
    
    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        """Handle switch join events."""
        switch = ev.switch
        dpid = switch.dp.id
        self.switches[dpid] = switch
        self.logger.info("Switch entered: %s", dpid)
    
    @set_ev_cls(event.EventSwitchLeave)
    def switch_leave_handler(self, ev):
        """Handle switch leave events."""
        switch = ev.switch
        dpid = switch.dp.id
        if dpid in self.switches:
            del self.switches[dpid]
            if dpid in self.mac_to_port:
                del self.mac_to_port[dpid]
            self.logger.info("Switch left: %s", dpid)
    
    @set_ev_cls(event.EventLinkAdd)
    def link_add_handler(self, ev):
        """Handle link add events."""
        link = ev.link
        src_dpid = link.src.dpid
        src_port = link.src.port_no
        dst_dpid = link.dst.dpid
        dst_port = link.dst.port_no
        
        if src_dpid not in self.links:
            self.links[src_dpid] = {}
        self.links[src_dpid][src_port] = (dst_dpid, dst_port)
        
        self.logger.info("Link added: %s:%s -> %s:%s", 
                         src_dpid, src_port, dst_dpid, dst_port)
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch features messages."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Initialize MAC table for this datapath
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        
        # Install the table-miss flow entry
        # Match any packet that hasn't been matched by previous entries
        match = parser.OFPMatch()
        # Send unmatched packets to the controller
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, 
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        self.logger.info("Switch %s connected and configured", dpid)
    
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add a flow entry to the datapath."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Construct flow_mod message
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, 
                                            actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                   priority=priority, match=match,
                                   instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                   match=match, instructions=inst)
        
        # Send flow_mod message to the datapath
        datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle packet-in messages from switches."""
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                             ev.msg.msg_len, ev.msg.total_len)
        
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        # Parse the packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        # Ignore LLDP packets
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        self.mac_to_port.setdefault(dpid, {})
        
        # Learn the MAC address to avoid flooding next time.
        self.mac_to_port[dpid][src] = in_port
        
        # Check if the destination MAC address is already known
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            # If destination not known, flood the packet
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install a flow to avoid packet_in next time if destination is known
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(eth_dst=dst, eth_src=src)
            # Verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod and packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        # Construct packet_out message and send it
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions,
                                 data=msg.data)
        datapath.send_msg(out)
    
    def _monitor(self):
        """Periodically monitor and print switch statistics."""
        while True:
            for dp in self.switches.values():
                self._request_stats(dp.dp)
            hub.sleep(10)
    
    def _request_stats(self, datapath):
        """Request statistics from the datapath."""
        self.logger.debug("send stats request: %016x", datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Request port statistics
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)
        
        # Request flow statistics
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
    
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        """Handle port statistics replies."""
        body = ev.msg.body
        
        self.logger.debug('datapath         port     '\
                          'rx-pkts  rx-bytes rx-error '\
                          'tx-pkts  tx-bytes tx-error')
        self.logger.debug('---------------- -------- '\
                          '-------- -------- -------- '\
                          '-------- -------- --------')
        
        for stat in sorted(body, key=lambda x: (x.dpid, x.port_no)):
            self.logger.debug('%016x %8x %8d %8d %8d %8d %8d %8d',
                             stat.dpid, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
    
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        """Handle flow statistics replies."""
        body = ev.msg.body
        
        self.logger.debug('datapath         '\
                          'in-port  eth-dst           '\
                          'out-port packets  bytes')
        self.logger.debug('---------------- '\
                          '-------- ----------------- '\
                          '-------- -------- --------')
        
        for stat in sorted([flow for flow in body if flow.priority == 1],
                          key=lambda x: (x.match['in_port'], x.match['eth_dst'])):
            self.logger.debug('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'],
                             stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)


if __name__ == '__main__':
    # This block is for testing purposes
    import sys
    from ryu.cmd import manager
    
    sys.argv.append(__file__)
    manager.main()