#
# ctypes_align.py
#
# Module for creating ctypes objects with alignments greater than
# ctypes normally supports.
#
# By Ross Ridge
# Public Domain
#

import ctypes

SimpleType = type(ctypes._SimpleCData)
ArrayType = type(ctypes.Array)
StructureType = type(ctypes.Structure)
UnionType = type(ctypes.Union)

class aligned_simple_type(SimpleType):
	def __mul__(self, length):
		return aligned_array_type(self._unalignedtype_,  length,
					  self._alignment_)

	def __new__(cls, name, bases, d):
		base = bases[0]
		base = getattr(base, "_unalignedtype_", base)
		d["_unalignedtype_"] = base
		d["__new__"] = _aligned__new__
		d["_baseclass_"] = base
		ret = SimpleType.__new__(cls, name, bases + (aligned_base,), d)
		ret._alignment_ = max(getattr(ret, "_alignment_", 1), 
				      ctypes.alignment(ret))
		return ret
		
class _aligned_array_type(ArrayType):
	def __mul__(self, length):
		return aligned_array_type(self._type_ * self._length_,
					  length, self._alignment_)

	def __init__(self, name, bases, d):
		self._alignment_ = max(getattr(self, "_alignment_", 1), 
				       ctypes.alignment(self))
		
class aligned_struct_type(StructureType):
	def __new__(cls, name, bases, d):
		base = bases[0]
		if hasattr(base, "_fields_"):
			offset = ctypes.sizeof(base)
		else:
			offset = 0
		pack = d.get("_pack_")
		uses_bitfields = False
		fields = d.get("_fields_", [])
		new_fields = []
		max_align = d.get("_alignment_")
		if max_align == None:
			max_align = getattr(base, "_alignment_", 1)
		for field in fields:
			if len(field) == 3:
				uses_bitfields = True
			typ = field[1]
			natural = ctypes.alignment(typ)
			align = max(natural, getattr(typ, "_alignment_", 1))
			if pack != None:
				natural = min(natural, pack)
				align = min(align, pack)
			if natural != align and uses_bitfields:
				raise ValueError("bit fields not supported")
			if (natural % align != 0
			    and offset % align != 0):
				padding = align - (offset % align)
				new_fields.append((("_padding_%d" % offset),
						   ctypes.c_char * padding))
				offset += padding
			new_fields.append(field)
			offset += ctypes.sizeof(typ)
			if align > max_align:
				max_align = align
		if offset % max_align != 0:
			padding = max_align - (offset % max_align)
			new_fields.append((("_padding_%d" % offset),
					   ctypes.c_char * padding))
		d["_alignment_"] = max_align
		if len(new_fields) != len(fields):
			d["_fields_"] = new_fields
		return StructureType.__new__(cls, name, bases, d)

	def __mul__(self, length):
		return aligned_array_type(self, length)

class aligned_union_type(UnionType):
	def __new__(cls, name, bases, d):
		base = bases[0]
		fields = d.get("_fields_", [])
		max_align = d.get("_alignment_")
		if max_align == None:
			max_align = getattr(base, "_alignment_", 1)
		max_size = 0
		for field in fields:
			typ = field[1]
			natural = ctypes.alignment(typ)
			align = max(natural, getattr(typ, "_alignment_", 1))
			max_align = max(max_align, align)
			max_size = max(max_size, ctypes.sizeof(typ))
			
		d["_alignment_"] = max_align
		if max_size % max_align != 0:
			d["_fields_"].append(("_padding",
					      ctypes.c_char * max_size))
		return UnionType.__new__(cls, name, bases, d)
	
	def __mul__(self, length):
		return aligned_array_type(self, length)

def aligned_alloc(typ, size, align = None, new = None):
	if size == None:
		size = typ.sizeof(typ)
	if align == None:
		align = typ._alignment_
	if new == None:
		a = typ.__new__(typ)
	else:
		a = new(typ)
	if (size == ctypes.sizeof(a)
	    and ctypes.addressof(a) % align == 0):
		#print("@@@ __new__ %s %08x" % (typ.__name__,
		#			       ctypes.addressof(a)))
		return a
	# base.__init__(a) # dunno if necessary
	ctypes.resize(a, size + align - 1)
	addr = ctypes.addressof(a)
	aligned = (addr + align - 1) // align * align
	# print("@@@ __new__ %s %08x %08x" % (typ.__name__, addr, aligned))
	if addr == aligned:
		return a
	if hasattr(typ, "from_buffer"):
		return typ.from_buffer(a, aligned - addr)
	r = typ.from_address(aligned)
	r._base_obj = a
	return r

def _aligned__new__(cls):
	return aligned_alloc(cls, ctypes.sizeof(cls),
			     new = cls._baseclass_.__new__)

class aligned_base(object):
	@classmethod
	def from_address(cls, addr):
		if addr % cls._alignment_ != 0:
			raise ValueError("address must be %d byte aligned"
					 % cls._alignment_)
		return cls._baseclass_.from_address(cls, addr)

	@classmethod
	def from_param(cls, addr):
		raise ValueError("%s objects may not be passed by value"
				 % cls.__name__)

class aligned_array(ctypes.Array, aligned_base):
	_baseclass_ = ctypes.Array
	_type_ = ctypes.c_byte
	_length_ = 1
	def __new__(cls, *ignore):
		return _aligned__new__(cls)

class aligned_struct(ctypes.Structure, aligned_base):
	__metaclass__ = aligned_struct_type
	_baseclass_ = ctypes.Structure
	def __new__(cls, *ignore):
		return _aligned__new__(cls)

class aligned_union(ctypes.Union, aligned_base):
	__metaclass__ = aligned_union_type
	_baseclass_ = ctypes.Union
	def __new__(cls, *ignore):
		return _aligned__new__(cls)
	
_aligned_type_cache = {}

def aligned_array_type(typ, length, alignment = None):
	natural = ctypes.alignment(typ)
	if alignment == None:
		alignment = typ._alignment_
	else:
		alignment = max(alignment, getattr(typ, "_alignment_", 1))
	
	if natural % alignment == 0:
		return typ * length
	eltsize = ctypes.sizeof(typ)
	eltalign = getattr(typ, "_alignment_", 1)
	if eltsize % eltalign != 0:
		raise TypeError("type %s can't have element alignment %d"
				" in an array" % (typ.__name__, alignment))
	key = (_aligned_array_type, (typ, length), alignment)
	ret = _aligned_type_cache.get(key)
	if ret == None:
		name = "%s_array_%d_aligned_%d" % (typ.__name__, length,
						   alignment)
		d = {"_type_": typ,
		     "_length_": length,
		     "_alignment_": alignment}
		ret = _aligned_array_type(name, (aligned_array,), d)
		_aligned_type_cache[key] = ret
	return ret

def _get_unaligned_type(typ, stopclass):	
	while (not typ.__dict__.get("_fields_")
	       and typ is not stopclass
	       and typ is not object):
		typ = super(typ)
	return typ

def aligned_type(typ, alignment):
	if ctypes.alignment(typ) % alignment == 0:
		return typ
	if issubclass(typ, ctypes.Array):
		return aligned_array_type(typ._type_, typ._length_, alignment)
	elif issubclass(typ, ctypes.Structure):
		factory = aligned_struct_type
		typ = _get_unaligned_type(typ, ctypes.Structure)
	elif issubclass(typ, ctypes.Union):
		factory = aligned_union_type
		typ = _get_unaligned_type(typ, ctypes.Union)
	elif issubclass(typ, ctypes._SimpleCData):
		factory = aligned_simple_type
		typ = getattr(typ, "_unalignedtype_", typ)
	else:
		raise TypeError("unsupported type %s" % typ)

	key = (factory, typ, alignment)
	atyp = _aligned_type_cache.get(key)
	if atyp == None:
		name = "%s_aligned_%d" % (typ.__name__, alignment)
		members = {"_alignment_": alignment}
		atyp = factory(name, (typ,), members)
		_aligned_type_cache[key] = atyp
	return atyp

def test():
	aligned_ulong = aligned_type(ctypes.c_ulong, 16)

	vector_float4 = aligned_type(ctypes.c_float * 4, 16)
	vector_double2 = aligned_array_type(ctypes.c_double, 2, 16)

	vector_float4_array_1024 = vector_float4 * 1024

	class struct1(ctypes.Structure):
		_fields_ = [("s1i", ctypes.c_int),
			    ("s1c", ctypes.c_char)]

	class struct2(struct1):
		_fields_ = [("s2c", ctypes.c_char)]


	class astruct1(aligned_struct):
		_fields_ = [("as1c", ctypes.c_char),
			    ("as1v", vector_float4),
			    ("as1c2", ctypes.c_char),
			    ("as1ul", aligned_ulong),
			    ("as1c3", ctypes.c_char),]

	class astruct2(astruct1):
		_fields_ = [("as2c", ctypes.c_char)]

	Feild = type(struct1.s1c)
	def dump_fields(a):
		print(a.__name__ + ":",
		      "natural", ctypes.alignment(a),
		      "align", getattr(a, "_alignment_", None),
		      "size", ctypes.sizeof(a))
		fields = [(name, getattr(a, name))
			  for name in dir(a)
			  if isinstance(getattr(a, name), Feild)]
		fields.sort(key = lambda x : x[1].offset)
		for (name, value) in fields:
			print("\t" + name, value)


	dump_fields(struct2)
	dump_fields(astruct2)

	a = [aligned_ulong()
	     for i in range(10)]

	for v in a:
		if ctypes.addressof(v) % 16 != 0:
			print("not aligned %08x" % ctypes.addressof(v))

	astruct2 * 10
	# import sys; sys.exit(0)

	b = vector_float4_array_1024()
	for i in range(1024):
		if ctypes.addressof(b[i]) % 16 != 0:
			print("not aligned b[%d] %08x" % (i, ctypes.addressof(b[i])))
			break
		b[i][0] = 1.0
		b[i][1] = -1.0
		b[i][2] = 1.0
		b[i][3] = 0

	for i in [1, 2, 4, 8, 16, 32]:
		typ = aligned_array_type(ctypes.c_double, 4, i)
		a = typ()
		print(i, typ, "%08x" % ctypes.addressof(a))

	class B(ctypes.Structure):
		_fields_ = [("b", ctypes.c_int)]

	class D(B):
		_fields_ = [("d", ctypes.c_int)]

	for name in dir(D):
		if name[0] != '_':
			print(name, getattr(D, name))
